import os

fp = 'public/BioRivet_Diagnostic_Tool_v2 (1).html'
with open(fp, 'r', encoding='utf-8') as f:
    code = f.read()

# Replace Button 1
code = code.replace(
    'onclick="genBatchPDF()">&#128196; Batch Summary PDF',
    'onclick="genBatchDOC()">&#128196; Batch Summary DOC'
)

# Replace Button 2
code = code.replace(
    'onclick="genAllStudentPDFs()">&#128196; All Student PDFs',
    'onclick="genAllStudentDOCs()">&#128196; All Student DOCs'
)

# Replace Header PDF
code = code.replace(
    '<span>Priority</span><span>PDF</span>',
    '<span>Priority</span><span>DOC</span>'
)

# Replace Student PDF button (need to be careful with quotes)
code = code.replace(
    "genStudentPDF('${s.name.replace(/\\\\/g,'\\\\\\\\').replace(/'/g,\"\\\\'\")}')\" style=\"padding:4px 8px;background:#B71C1C;color:white;border:none;border-radius:5px;font-size:11px;font-weight:600;cursor:pointer\">&#128196; PDF",
    "genStudentDOC('${s.name.replace(/\\\\/g,'\\\\\\\\').replace(/'/g,\"\\\\'\")}')\" style=\"padding:4px 8px;background:#2563eb;color:white;border:none;border-radius:5px;font-size:11px;font-weight:600;cursor:pointer\">&#128196; DOC"
)

# Replace comments
code = code.replace(
    '// Store plain-text plan for Excel export and PDF',
    '// Store plain-text plan for Excel export and DOC'
)

# Replace Functions
start_str = '// INDIVIDUAL STUDENT PDF'
end_str = 'function showErr(type, msg)'

start_idx = code.find(start_str)
end_idx = code.find(end_str)

if start_idx == -1 or end_idx == -1:
    print("Could not find start or end block!")
    exit(1)

new_funcs = """// INDIVIDUAL STUDENT DOC
function genStudentDOC(name) {
  const s = RPT.studentReports.find(x => x.name === name);
  if(!s){alert('Student not found');return;}
  const KEY = QP.questions.map(q=>q.ans);

  const tierLabel = s.marksPct < 10 ? 'Critical' : s.marksPct < 35 ? 'High Risk' : s.marksPct < 55 ? 'Medium Risk' : 'Low Risk';
  const marksColor = s.priority==='high'?'#B71C1C':s.priority==='medium'?'#E65100':'#1B5E20';

  const chapRows = Object.entries(RPT.chapGroups).map(([ch, indices]) => {
    const cstat = RPT.chapterStats[ch];
    const cw2 = s.chapWrong[ch] || 0;
    const qcount = indices.length;
    const correct = qcount - cw2 - (s.chapUnattempted[ch] || 0);
    const pct = qcount>0 ? Math.round((correct/qcount)*100) : 0;
    const wrongRate = qcount>0 ? Math.round((cw2/qcount)*100) : 0;
    const badge = cstat.level==='critical'?'[!] Critical':cstat.level==='needs'?'&#8594; Review':'[+] Strong';
    const bc = pct>=70?'#27ae60':pct>=50?'#f39c12':'#e74c3c';
    return `
      <tr>
        <td style="padding:10px; border-bottom:1px solid #ddd; font-family:Arial,sans-serif;"><strong>${ch}</strong></td>
        <td style="padding:10px; border-bottom:1px solid #ddd; color:#666; font-family:Arial,sans-serif;">${correct}/${qcount} correct (${wrongRate}% wrong)<br><span style="color:${bc};font-size:11px">${badge}</span></td>
        <td style="padding:10px; border-bottom:1px solid #ddd; width:200px;">
          <div style="background:#e2e8f0; width:100%; height:12px; border-radius:6px; overflow:hidden;">
            <div style="background:${bc}; width:${Math.max(pct,2)}%; height:100%;"></div>
          </div>
        </td>
        <td style="padding:10px; border-bottom:1px solid #ddd; font-weight:bold; color:${bc}; font-family:Arial,sans-serif;">${pct}%</td>
      </tr>
    `;
  }).join('');

  const cols = 10;
  let gridHtml = '<table width="100%" style="border-collapse:collapse; text-align:center; font-family:Arial,sans-serif; font-size:11px;">';
  for (let i = 0; i < QP.questions.length; i += cols) {
    gridHtml += '<tr>';
    for (let j = 0; j < cols; j++) {
      const qi = i + j;
      if (qi < QP.questions.length) {
        const q = QP.questions[qi];
        const ans = s.answers[qi];
        const correctAns = KEY[qi];
        const ok = ans === correctAns;
        const blank = ans === '';
        const bg = blank ? '#f0f0f5' : ok ? '#dcfce7' : '#fee2e2';
        const tc = blank ? '#64748b' : ok ? '#15803d' : '#b91c1c';
        const txt = blank ? '-' : ok ? ans : `${correctAns} &rarr; ${ans}`;
        gridHtml += `<td style="border:3px solid white; background:${bg}; color:${tc}; padding:10px; width:10%;">
          <div style="font-size:9px; color:#888; margin-bottom:4px;">Q${q.qno}</div>
          <div style="font-weight:bold; font-size:12px;">${txt}</div>
        </td>`;
      } else {
        gridHtml += '<td style="border:3px solid white; width:10%;"></td>';
      }
    }
    gridHtml += '</tr>';
  }
  gridHtml += '</table>';

  const html = `
  <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
  <head>
    <meta charset='utf-8'>
    <title>Diagnostic Report - ${s.name}</title>
  </head>
  <body style="font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6;">
    <div style="background-color: #1F3864; color: white; padding: 25px; margin-bottom: 20px;">
      <h1 style="margin:0; color:white; font-size:24px;">BioRivet NEET Diagnostic Report</h1>
      <p style="margin:5px 0 0 0; color:#cbd5e1; font-size:12px;">Generated: ${new Date().toLocaleDateString('en-IN')} | Know More. Fear Less.</p>
    </div>
    
    <div style="padding: 0 20px;">
      <h2 style="font-size: 28px; margin: 0 0 5px 0; color:#1F3864;">${s.name}</h2>
      <p style="color:#666; margin-top:0; font-size:12px;">Individual Diagnostic Report | +4 Correct / -1 Wrong</p>
      
      <table width="100%" cellpadding="15" cellspacing="10" style="margin-bottom: 20px;">
        <tr>
          <td align="center" style="background:#f0f4fb; border-radius:8px; border:1px solid #e2e8f0; width:33%;">
            <span style="font-size:11px; color:#666; text-transform:uppercase; font-weight:bold;">NEET Marks</span><br>
            <strong style="font-size:26px; color:${marksColor};">${s.neetMarks} / ${s.maxMarks}</strong><br>
            <span style="font-size:11px; color:#888;">${s.totalCorrect} correct, ${s.totalWrong} wrong</span>
          </td>
          <td align="center" style="background:#f0f4fb; border-radius:8px; border:1px solid #e2e8f0; width:33%;">
            <span style="font-size:11px; color:#666; text-transform:uppercase; font-weight:bold;">Accuracy</span><br>
            <strong style="font-size:26px; color:#1F3864;">${s.pct}%</strong>
          </td>
          <td align="center" style="background:#f0f4fb; border-radius:8px; border:1px solid #e2e8f0; width:33%;">
            <span style="font-size:11px; color:#666; text-transform:uppercase; font-weight:bold;">Priority</span><br>
            <strong style="font-size:26px; color:${marksColor}; text-transform:uppercase;">${s.priority}</strong>
          </td>
        </tr>
      </table>

      <h3 style="color:#1F3864; border-bottom:2px solid #e2e8f0; padding-bottom:8px;">Chapter Performance</h3>
      <table width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 30px; border-collapse:collapse;">
        ${chapRows}
      </table>

      <br clear=all style='mso-special-character:line-break;page-break-before:always'>

      <h3 style="color:#1F3864; border-bottom:2px solid #e2e8f0; padding-bottom:8px;">Answer Analysis</h3>
      <p style="font-size:11px; color:#666;">Correct answers are green. Wrong answers show [Key &rarr; Your Answer] in red. Blanks are grey.</p>
      ${gridHtml}

      <br clear=all style='mso-special-character:line-break;page-break-before:always'>

      <div style="background:#1F3864; color:white; padding:15px; border-radius:6px; margin-bottom:15px;">
        <h3 style="margin:0; color:white; font-size:18px;">Personalised Action Plan</h3>
        <span style="font-size:12px; color:#cbd5e1;">${tierLabel} &middot; Focus: ${s.w1} &middot; ${s.w2}</span>
      </div>
      
      <div style="padding:10px; font-size:13px; color:#333;">
        ${s._planText}
      </div>
      
      ${s.topSubs && s.topSubs.length > 0 ? `
        <h4 style="margin-top:25px; color:#1F3864;">Key Sub-Topics to Revise:</h4>
        <ul style="font-size:13px; color:#444;">
          ${s.topSubs.map(([sub,w])=>`<li style="margin-bottom:6px;"><strong>${sub}</strong> (${w} wrong)</li>`).join('')}
        </ul>
      ` : ''}

    </div>
  </body>
  </html>
  `;

  const blob = new Blob(['\\ufeff', html], { type: 'application/msword' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'BioRivet_' + s.name.replace(/\\s+/g,'_') + '_Report.doc';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ══════════════════════════════════════════════════════════════
// BATCH SUMMARY DOC
// ══════════════════════════════════════════════════════════════
function genBatchDOC() {
  if(!RPT){alert('Generate report first.');return;}
  const r = RPT;
  const avgPct = Math.round((r.avgNeetMarks/(r.totalQ*4))*100);

  const chapRows = Object.entries(r.chapterStats).map(([ch, cs]) => {
    const pct = Math.round(cs.pct*100);
    const bc = cs.level==='critical'?'#e74c3c':cs.level==='needs'?'#f39c12':'#27ae60';
    const badge = cs.level==='critical'?'[!] Critical':cs.level==='needs'?'&#8594; Attention':'[+] Strong';
    return `
      <tr>
        <td style="padding:10px; border-bottom:1px solid #ddd; font-family:Arial,sans-serif;"><strong>${ch}</strong></td>
        <td style="padding:10px; border-bottom:1px solid #ddd; color:#666; font-family:Arial,sans-serif;">${cs.totalWrong}/${cs.max} wrong</td>
        <td style="padding:10px; border-bottom:1px solid #ddd; width:150px;">
          <div style="background:#e2e8f0; width:100%; height:12px; border-radius:6px; overflow:hidden;">
            <div style="background:${bc}; width:${Math.max(pct,2)}%; height:100%;"></div>
          </div>
        </td>
        <td style="padding:10px; border-bottom:1px solid #ddd; font-weight:bold; color:${bc}; font-family:Arial,sans-serif;">${pct}%</td>
        <td style="padding:10px; border-bottom:1px solid #ddd; color:${bc}; font-size:12px; font-family:Arial,sans-serif;">${badge}</td>
      </tr>
    `;
  }).join('');

  const topErr = r.mem>=r.con&&r.mem>=r.app?'Memory':r.con>=r.app?'Conceptual':'Application';
  
  const hiStudents = [...r.studentReports].filter(s=>s.priority==='high').sort((a,b)=>b.totalWrong-a.totalWrong).slice(0,10);
  const hiRows = hiStudents.length === 0 
    ? '<tr><td colspan="4" style="padding:15px; color:#27ae60; font-family:Arial,sans-serif;">No high-risk students. Excellent batch performance!</td></tr>'
    : hiStudents.map(s => `
      <tr>
        <td style="padding:10px; border-bottom:1px solid #eee; font-family:Arial,sans-serif;"><strong>${s.name}</strong></td>
        <td style="padding:10px; border-bottom:1px solid #eee; color:#666; font-family:Arial,sans-serif;">${s.neetMarks}/${s.maxMarks}</td>
        <td style="padding:10px; border-bottom:1px solid #eee; color:#666; font-family:Arial,sans-serif;">${s.w1}</td>
        <td style="padding:10px; border-bottom:1px solid #eee; color:#e74c3c; font-weight:bold; font-family:Arial,sans-serif;">${s.totalWrong} wrong</td>
      </tr>
    `).join('');

  const html = `
  <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
  <head>
    <meta charset='utf-8'>
    <title>Batch Summary Report</title>
  </head>
  <body style="font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6;">
    <div style="background-color: #1F3864; color: white; padding: 25px; margin-bottom: 20px;">
      <h1 style="margin:0; color:white; font-size:24px;">BioRivet Batch Diagnostic Summary</h1>
      <p style="margin:5px 0 0 0; color:#cbd5e1; font-size:12px;">Generated: ${new Date().toLocaleDateString('en-IN')} | Institute Confidential</p>
    </div>
    
    <div style="padding: 0 20px;">
      <table width="100%" cellpadding="15" cellspacing="10" style="margin-bottom: 30px;">
        <tr>
          <td align="center" style="background:#f0f4fb; border-radius:8px; border:1px solid #e2e8f0; width:25%;">
            <span style="font-size:11px; color:#666; text-transform:uppercase; font-weight:bold;">Students</span><br>
            <strong style="font-size:26px; color:#1F3864;">${r.N}</strong>
          </td>
          <td align="center" style="background:#f0f4fb; border-radius:8px; border:1px solid #e2e8f0; width:25%;">
            <span style="font-size:11px; color:#666; text-transform:uppercase; font-weight:bold;">Avg NEET Marks</span><br>
            <strong style="font-size:26px; color:#1F3864;">${r.avgNeetMarks} / ${r.totalQ*4}</strong>
          </td>
          <td align="center" style="background:#fee2e2; border-radius:8px; border:1px solid #fecaca; width:25%;">
            <span style="font-size:11px; color:#666; text-transform:uppercase; font-weight:bold;">High Risk</span><br>
            <strong style="font-size:26px; color:#b91c1c;">${r.highRisk}</strong>
          </td>
          <td align="center" style="background:#fff7ed; border-radius:8px; border:1px solid #fed7aa; width:25%;">
            <span style="font-size:11px; color:#666; text-transform:uppercase; font-weight:bold;">Weakest Chapter</span><br>
            <strong style="font-size:18px; color:#c2410c;">${r.worstCh}</strong>
          </td>
        </tr>
      </table>

      <h3 style="color:#1F3864; border-bottom:2px solid #e2e8f0; padding-bottom:8px;">Chapter-Wise Error Analysis</h3>
      <table width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 30px; border-collapse:collapse;">
        ${chapRows}
      </table>

      <br clear=all style='mso-special-character:line-break;page-break-before:always'>

      <h3 style="color:#1F3864; border-bottom:2px solid #e2e8f0; padding-bottom:8px;">Top High-Risk Students</h3>
      <table width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 30px; border-collapse:collapse; background:#f8fafc; border:1px solid #e2e8f0;">
        ${hiRows}
      </table>

      <div style="background:#e0e7ff; padding:20px; border-radius:8px; border-left:5px solid #4338ca; margin-top:20px;">
        <h3 style="margin-top:0; color:#3730a3; font-size:18px;">Key Recommendations</h3>
        <ol style="margin-bottom:0; font-size:13px; color:#333; padding-left:20px;">
          <li style="margin-bottom:8px;">Schedule a dedicated revision class on <strong>${r.worstCh}</strong> before next test cycle.</li>
          <li style="margin-bottom:8px;"><strong>${r.highRisk}</strong> high-risk students need individual counselling this week.</li>
          <li style="margin-bottom:8px;">Dominant error type is <strong>${topErr}</strong>. ${topErr==='Conceptual'?'Focus on understanding mechanisms, not rote facts.':topErr==='Application'?'Students understand concepts but struggle to apply — more timed MCQ practice.':'Spaced repetition and active recall drills will help.'}</li>
          <li>Re-test all students on <strong>${r.worstCh}</strong> within 7 days.</li>
        </ol>
      </div>

    </div>
  </body>
  </html>
  `;

  const blob = new Blob(['\\ufeff', html], { type: 'application/msword' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'BioRivet_Batch_Summary.doc';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// All student DOCs
async function genAllStudentDOCs() {
  if(!RPT){alert('Generate report first.');return;}
  const sorted=[...RPT.studentReports].sort((a,b)=>b.neetMarks-a.neetMarks);
  for(let i=0;i<sorted.length;i++){
    genStudentDOC(sorted[i].name);
    await new Promise(r=>setTimeout(r,500));
  }
}
"""

new_code = code[:start_idx] + new_funcs + "\\n" + code[end_idx:]

with open(fp, 'w', encoding='utf-8') as f:
    f.write(new_code)

print("SUCCESS")
