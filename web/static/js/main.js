// OpenClaw Drug Web 界面 JavaScript

// 文献分析表单提交
document.getElementById('literatureForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const keyword = document.getElementById('keyword').value;
    const max_papers = document.getElementById('max_papers').value;
    const days = document.getElementById('days').value;
    
    // 显示加载状态
    document.getElementById('literatureLoading').style.display = 'block';
    document.getElementById('literatureResults').style.display = 'none';
    
    try {
        const response = await fetch('/api/literature/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ keyword, max_papers, days })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayLiteratureResults(result);
        } else {
            alert('分析失败: ' + result.error);
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    } finally {
        document.getElementById('literatureLoading').style.display = 'none';
    }
});

// 显示文献分析结果
function displayLiteratureResults(result) {
    const statsHtml = `
        <div class="row">
            <div class="col-md-3">
                <div class="result-card">
                    <h6>总文献数</h6>
                    <h3 class="text-primary">${result.total_papers}</h3>
                </div>
            </div>
        </div>
    `;
    document.getElementById('literatureStats').innerHTML = statsHtml;
    
    // 显示热点主题
    let topicsHtml = '<div class="row">';
    let count = 0;
    for (const [topic, cnt] of Object.entries(result.trending_topics)) {
        if (count >= 8) break;
        topicsHtml += `
            <div class="col-md-3 mb-2">
                <span class="badge bg-primary me-1">${cnt}</span> ${topic}
            </div>
        `;
        count++;
    }
    topicsHtml += '</div>';
    document.getElementById('trendingTopics').innerHTML = topicsHtml;
    
    // 显示关键发现
    let findingsHtml = '';
    result.key_findings.slice(0, 10).forEach((finding, index) => {
        findingsHtml += `
            <div class="result-card">
                <strong>${index + 1}. </strong>${finding}
            </div>
        `;
    });
    document.getElementById('keyFindings').innerHTML = findingsHtml;
    
    // 显示报告
    document.getElementById('literatureReport').textContent = result.report_content;
    document.getElementById('literatureReport').style.display = 'block';
    
    // 设置下载链接
    const downloadBtn = document.getElementById('downloadLiteratureReport');
    downloadBtn.style.display = 'inline-block';
    downloadBtn.onclick = () => {
        window.open(result.download_url, '_blank');
    };
    
    document.getElementById('literatureResults').style.display = 'block';
}

// 单个ADMET预测表单提交
document.getElementById('singleAdmetForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const smiles = document.getElementById('smiles').value;
    
    document.getElementById('admetLoading').style.display = 'block';
    document.getElementById('admetResults').style.display = 'none';
    
    try {
        const response = await fetch('/api/admet/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ smiles })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displaySingleAdmetResult(result);
        } else {
            alert('预测失败: ' + result.error);
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    } finally {
        document.getElementById('admetLoading').style.display = 'none';
    }
});

// 批量ADMET预测表单提交
document.getElementById('batchAdmetForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('admetFile');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    document.getElementById('admetLoading').style.display = 'block';
    document.getElementById('admetResults').style.display = 'none';
    
    try {
        const response = await fetch('/api/admet/predict', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayBatchAdmetResult(result);
        } else {
            alert('预测失败: ' + result.error);
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    } finally {
        document.getElementById('admetLoading').style.display = 'none';
    }
});

// 显示单个ADMET预测结果
function displaySingleAdmetResult(result) {
    let decisionClass = '';
    if (result.decision === '优先开发') decisionClass = 'text-success';
    else if (result.decision === '进一步优化') decisionClass = 'text-warning';
    else if (result.decision === '谨慎评估') decisionClass = 'text-orange';
    else decisionClass = 'text-danger';
    
    const summaryHtml = `
        <div class="row">
            <div class="col-md-3">
                <div class="result-card">
                    <h6>综合评分</h6>
                    <h3 class="text-primary">${result.overall_score.toFixed(3)}</h3>
                </div>
            </div>
            <div class="col-md-3">
                <div class="result-card">
                    <h6>决策建议</h6>
                    <h3 class="${decisionClass}">${result.decision}</h3>
                </div>
            </div>
            <div class="col-md-3">
                <div class="result-card">
                    <h6>口服生物利用度</h6>
                    <h4>${result.detailed_results.absorption.oral_bioavailability}</h4>
                </div>
            </div>
            <div class="col-md-3">
                <div class="result-card">
                    <h6>总体毒性风险</h6>
                    <h4>${result.detailed_results.toxicity.overall_toxicity_risk}</h4>
                </div>
            </div>
        </div>
    `;
    
    const details = result.detailed_results;
    const detailsHtml = `
        <div class="card mb-3">
            <div class="card-header">
                <h5>理化性质</h5>
            </div>
            <div class="card-body">
                <table class="table table-striped">
                    <tr><td>分子量</td><td>${details.physicochemical_properties.molecular_weight.toFixed(1)}</td></tr>
                    <tr><td>LogP</td><td>${details.physicochemical_properties.logp.toFixed(2)}</td></tr>
                    <tr><td>氢键供体</td><td>${details.physicochemical_properties.h_donors}</td></tr>
                    <tr><td>氢键受体</td><td>${details.physicochemical_properties.h_acceptors}</td></tr>
                    <tr><td>TPSA</td><td>${details.physicochemical_properties.tpsa.toFixed(1)}</td></tr>
                    <tr><td>QED</td><td>${details.physicochemical_properties.qed.toFixed(3)}</td></tr>
                    <tr><td>Lipinski规则违反</td><td>${details.physicochemical_properties.lipinski_violations}</td></tr>
                </table>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card mb-3">
                    <div class="card-header">
                        <h5>吸收性质</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>口服生物利用度:</strong> ${details.absorption.oral_bioavailability}</p>
                        <p><strong>Caco-2渗透性:</strong> ${details.absorption.caco2_permeability}</p>
                        <p><strong>肠道吸收:</strong> ${details.absorption.intestinal_absorption}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card mb-3">
                    <div class="card-header">
                        <h5>分布性质</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>血脑屏障穿透性:</strong> ${details.distribution.bbb_permeability}</p>
                        <p><strong>血浆蛋白结合率:</strong> ${details.distribution.plasma_protein_binding}</p>
                        <p><strong>表观分布容积:</strong> ${details.distribution.volume_of_distribution}</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card mb-3">
                    <div class="card-header">
                        <h5>代谢性质</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>CYP抑制剂:</strong> ${details.metabolism.cyp_inhibitors.join(', ')}</p>
                        <p><strong>CYP抑制风险:</strong> ${details.metabolism.cyp_inhibition_risk}</p>
                        <p><strong>代谢稳定性:</strong> ${details.metabolism.metabolic_stability}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card mb-3">
                    <div class="card-header">
                        <h5>毒性性质</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>肝毒性:</strong> ${details.toxicity.hepatotoxicity}</p>
                        <p><strong>hERG抑制:</strong> ${details.toxicity.herg_inhibition}</p>
                        <p><strong>Ames致突变性:</strong> ${details.toxicity.ames_mutagenicity}</p>
                        <p><strong>总体毒性风险:</strong> ${details.toxicity.overall_toxicity_risk}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('admetSummary').innerHTML = summaryHtml;
    document.getElementById('admetDetails').innerHTML = detailsHtml;
    document.getElementById('admetReport').textContent = result.report_content;
    document.getElementById('admetReport').style.display = 'block';
    
    // 设置下载链接
    const downloadBtn = document.getElementById('downloadAdmetResults');
    downloadBtn.style.display = 'inline-block';
    downloadBtn.onclick = () => {
        window.open(result.download_url, '_blank');
    };
    
    document.getElementById('admetResults').style.display = 'block';
}

// 显示批量ADMET预测结果
function displayBatchAdmetResult(result) {
    const summaryHtml = `
        <div class="row">
            <div class="col-md-3">
                <div class="result-card">
                    <h6>总化合物数</h6>
                    <h3 class="text-primary">${result.total_compounds}</h3>
                </div>
            </div>
            <div class="col-md-3">
                <div class="result-card">
                    <h6>平均评分</h6>
                    <h3>${result.average_score.toFixed(2)}</h3>
                </div>
            </div>
            <div class="col-md-3">
                <div class="result-card">
                    <h6>优先开发</h6>
                    <h3 class="text-success">${result.statistics.priority}</h3>
                </div>
            </div>
            <div class="col-md-3">
                <div class="result-card">
                    <h6>建议淘汰</h6>
                    <h3 class="text-danger">${result.statistics.elimination}</h3>
                </div>
            </div>
        </div>
        
        <div class="mt-4">
            <h5>结果分布</h5>
            <canvas id="admetChart" width="400" height="200"></canvas>
        </div>
    `;
    
    // 显示预览表格
    let previewHtml = `
        <h5 class="mt-4">结果预览 (前20条)</h5>
        <div class="table-responsive">
            <table class="table table-striped table-sm">
                <thead>
                    <tr>
                        <th>SMILES</th>
                        <th>综合评分</th>
                        <th>决策</th>
                        <th>分子量</th>
                        <th>LogP</th>
                        <th>毒性风险</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    result.results_preview.forEach(row => {
        let decisionClass = '';
        if (row.admet_decision === '优先开发') decisionClass = 'table-success';
        else if (row.admet_decision === '建议淘汰') decisionClass = 'table-danger';
        
        previewHtml += `
            <tr class="${decisionClass}">
                <td><small>${row.smiles}</small></td>
                <td>${row.overall_score.toFixed(3)}</td>
                <td>${row.admet_decision}</td>
                <td>${row.physchem_molecular_weight.toFixed(1)}</td>
                <td>${row.physchem_logp.toFixed(2)}</td>
                <td>${row.toxicity_overall_toxicity_risk}</td>
            </tr>
        `;
    });
    
    previewHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    document.getElementById('admetSummary').innerHTML = summaryHtml;
    document.getElementById('admetDetails').innerHTML = previewHtml;
    document.getElementById('admetReport').style.display = 'none';
    
    // 绘制图表
    const ctx = document.getElementById('admetChart').getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['优先开发', '进一步优化', '谨慎评估', '建议淘汰'],
            datasets: [{
                data: [
                    result.statistics.priority,
                    result.statistics.optimization,
                    result.statistics.evaluation,
                    result.statistics.elimination
                ],
                backgroundColor: [
                    '#28a745',
                    '#ffc107',
                    '#fd7e14',
                    '#dc3545'
                ]
            }]
        }
    });
    
    // 设置下载链接
    const downloadBtn = document.getElementById('downloadAdmetResults');
    downloadBtn.style.display = 'inline-block';
    downloadBtn.onclick = () => {
        window.open(result.download_url, '_blank');
    };
    
    document.getElementById('admetResults').style.display = 'block';
}

// 虚拟筛选表单提交
document.getElementById('screeningForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('target_pdb', document.getElementById('targetPdb').files[0]);
    formData.append('library_file', document.getElementById('libraryFile').files[0]);
    formData.append('center_x', document.getElementById('centerX').value);
    formData.append('center_y', document.getElementById('centerY').value);
    formData.append('center_z', document.getElementById('centerZ').value);
    formData.append('size_x', document.getElementById('sizeX').value);
    formData.append('size_y', document.getElementById('sizeY').value);
    formData.append('size_z', document.getElementById('sizeZ').value);
    formData.append('top_n', document.getElementById('topN').value);
    
    document.getElementById('screeningLoading').style.display = 'block';
    document.getElementById('screeningResults').style.display = 'none';
    
    try {
        const response = await fetch('/api/screening/run', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayScreeningResults(result);
        } else {
            alert('筛选失败: ' + result.error);
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    } finally {
        document.getElementById('screeningLoading').style.display = 'none';
    }
});

// 显示虚拟筛选结果
function displayScreeningResults(result) {
    const summaryHtml = `
        <div class="row">
            <div class="col-md-4">
                <div class="result-card">
                    <h6>总化合物数</h6>
                    <h3 class="text-primary">${result.total_compounds}</h3>
                </div>
            </div>
            <div class="col-md-4">
                <div class="result-card">
                    <h6>最佳结合能</h6>
                    <h3 class="text-success">${result.best_affinity.toFixed(2)} kcal/mol</h3>
                </div>
            </div>
            <div class="col-md-4">
                <div class="result-card">
                    <h6>结合能 < -7 kcal/mol</h6>
                    <h3>${result.top_candidates.filter(c => c.binding_affinity <= -7).length}</h3>
                </div>
            </div>
        </div>
    `;
    
    // 显示Top候选化合物表格
    let candidatesHtml = `
        <h5 class="mt-4">Top 候选化合物</h5>
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>SMILES</th>
                        <th>结合能 (kcal/mol)</th>
                        <th>分子量</th>
                        <th>LogP</th>
                        <th>QED</th>
                        <th>ADMET风险</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    result.top_candidates.forEach(candidate => {
        let affinityClass = candidate.binding_affinity <= -8 ? 'table-success' : 
                           candidate.binding_affinity <= -7 ? 'table-warning' : '';
        
        candidatesHtml += `
            <tr class="${affinityClass}">
                <td>${candidate.rank}</td>
                <td><small>${candidate.smiles}</small></td>
                <td><strong>${candidate.binding_affinity.toFixed(2)}</strong></td>
                <td>${candidate.molecular_weight.toFixed(1)}</td>
                <td>${candidate.logp.toFixed(2)}</td>
                <td>${candidate.qed.toFixed(3)}</td>
                <td>${candidate.admet_risk_assessment}</td>
            </tr>
        `;
    });
    
    candidatesHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    document.getElementById('screeningSummary').innerHTML = summaryHtml;
    document.getElementById('topCandidates').innerHTML = candidatesHtml;
    document.getElementById('screeningReport').textContent = result.report_content;
    document.getElementById('screeningReport').style.display = 'block';
    
    // 设置下载链接
    document.getElementById('downloadScreeningResults').style.display = 'inline-block';
    document.getElementById('downloadScreeningResults').onclick = () => {
        window.open(result.download_url, '_blank');
    };
    
    document.getElementById('downloadScreeningReport').style.display = 'inline-block';
    document.getElementById('downloadScreeningReport').onclick = () => {
        window.open(result.report_download_url, '_blank');
    };
    
    document.getElementById('screeningResults').style.display = 'block';
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 检查API健康状态
    fetch('/api/health')
        .then(response => response.json())
        .then(data => {
            console.log('API状态:', data);
        })
        .catch(error => {
            console.error('API连接失败:', error);
            alert('API连接失败，请确保后端服务正常运行');
        });
});