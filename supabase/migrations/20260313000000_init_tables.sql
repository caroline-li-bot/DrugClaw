-- 初始化Supabase数据库表结构

-- 1. 用户任务表
CREATE TABLE IF NOT EXISTS user_tasks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    task_type TEXT NOT NULL, -- literature, admet, screening
    status TEXT NOT NULL DEFAULT 'pending', -- pending, running, completed, failed
    parameters JSONB NOT NULL,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 化合物库表
CREATE TABLE IF NOT EXISTS compound_libraries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    total_compounds INTEGER NOT NULL DEFAULT 0,
    source TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 化合物表
CREATE TABLE IF NOT EXISTS compounds (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    library_id UUID REFERENCES compound_libraries(id) ON DELETE CASCADE,
    smiles TEXT NOT NULL,
    molecular_weight NUMERIC,
    logp NUMERIC,
    h_donors INTEGER,
    h_acceptors INTEGER,
    tpsa NUMERIC,
    qed NUMERIC,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(library_id, smiles)
);

-- 4. ADMET预测结果表
CREATE TABLE IF NOT EXISTS admet_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    compound_id UUID REFERENCES compounds(id) ON DELETE CASCADE,
    smiles TEXT NOT NULL,
    overall_score NUMERIC,
    admet_decision TEXT,
    absorption JSONB,
    distribution JSONB,
    metabolism JSONB,
    excretion JSONB,
    toxicity JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. 虚拟筛选任务表
CREATE TABLE IF NOT EXISTS screening_jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    target_name TEXT,
    target_pdb TEXT NOT NULL,
    binding_site JSONB NOT NULL,
    library_id UUID REFERENCES compound_libraries(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    total_compounds INTEGER,
    completed_compounds INTEGER DEFAULT 0,
    best_affinity NUMERIC,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. 虚拟筛选结果表
CREATE TABLE IF NOT EXISTS screening_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES screening_jobs(id) ON DELETE CASCADE,
    compound_id UUID REFERENCES compounds(id) ON DELETE CASCADE,
    smiles TEXT NOT NULL,
    binding_affinity NUMERIC NOT NULL,
    rank INTEGER,
    priority_score NUMERIC,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. 文献分析任务表
CREATE TABLE IF NOT EXISTS literature_jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    keyword TEXT NOT NULL,
    max_papers INTEGER NOT NULL DEFAULT 50,
    days INTEGER NOT NULL DEFAULT 365,
    total_papers INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
    key_findings JSONB,
    trending_topics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. 文献记录表
CREATE TABLE IF NOT EXISTS literature_papers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES literature_jobs(id) ON DELETE CASCADE,
    pmid TEXT UNIQUE,
    title TEXT,
    abstract TEXT,
    authors JSONB,
    journal TEXT,
    year TEXT,
    doi TEXT,
    url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_compounds_smiles ON compounds(smiles);
CREATE INDEX IF NOT EXISTS idx_admet_results_smiles ON admet_results(smiles);
CREATE INDEX IF NOT EXISTS idx_screening_results_job_id ON screening_results(job_id);
CREATE INDEX IF NOT EXISTS idx_screening_results_binding_affinity ON screening_results(binding_affinity);
CREATE INDEX IF NOT EXISTS idx_user_tasks_user_id ON user_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_literature_jobs_keyword ON literature_jobs(keyword);

-- 启用RLS (Row Level Security)
ALTER TABLE user_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE compound_libraries ENABLE ROW LEVEL SECURITY;
ALTER TABLE compounds ENABLE ROW LEVEL SECURITY;
ALTER TABLE admet_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE screening_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE screening_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE literature_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE literature_papers ENABLE ROW LEVEL SECURITY;

-- 创建策略 (允许公共访问，生产环境需要调整)
CREATE POLICY "Allow public access to user_tasks" ON user_tasks FOR ALL USING (true);
CREATE POLICY "Allow public access to compound_libraries" ON compound_libraries FOR ALL USING (true);
CREATE POLICY "Allow public access to compounds" ON compounds FOR ALL USING (true);
CREATE POLICY "Allow public access to admet_results" ON admet_results FOR ALL USING (true);
CREATE POLICY "Allow public access to screening_jobs" ON screening_jobs FOR ALL USING (true);
CREATE POLICY "Allow public access to screening_results" ON screening_results FOR ALL USING (true);
CREATE POLICY "Allow public access to literature_jobs" ON literature_jobs FOR ALL USING (true);
CREATE POLICY "Allow public access to literature_papers" ON literature_papers FOR ALL USING (true);

-- 存储化合物的函数
CREATE OR REPLACE FUNCTION insert_compound(
    p_library_id UUID,
    p_smiles TEXT,
    p_molecular_weight NUMERIC,
    p_logp NUMERIC,
    p_h_donors INTEGER,
    p_h_acceptors INTEGER,
    p_tpsa NUMERIC,
    p_qed NUMERIC
) RETURNS UUID AS $$
DECLARE
    compound_id UUID;
BEGIN
    INSERT INTO compounds (library_id, smiles, molecular_weight, logp, h_donors, h_acceptors, tpsa, qed)
    VALUES (p_library_id, p_smiles, p_molecular_weight, p_logp, p_h_donors, p_h_acceptors, p_tpsa, p_qed)
    ON CONFLICT (library_id, smiles) DO UPDATE
    SET molecular_weight = EXCLUDED.molecular_weight,
        logp = EXCLUDED.logp,
        h_donors = EXCLUDED.h_donors,
        h_acceptors = EXCLUDED.h_acceptors,
        tpsa = EXCLUDED.tpsa,
        qed = EXCLUDED.qed
    RETURNING id INTO compound_id;
    
    RETURN compound_id;
END;
$$ LANGUAGE plpgsql;