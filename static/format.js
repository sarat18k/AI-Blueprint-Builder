/**
 * Shared formatting utilities for A2A agent outputs.
 * Converts structured JSON into semantic, readable HTML.
 */

const AGENT_LABELS = {
  ResearchAgent:  'Market Research',
  AnalysisAgent:  'Competitor Analysis',
  ProductAgent:   'Product Requirements',
  MarketingAgent: 'Go-to-Market Strategy',
  ArchitectAgent: 'System Architecture',
  CodeAgent:      'MVP Code Generation',
  PitchAgent:     'Investor Pitch Deck',
  DocumentAgent:  'Document Export',
};

function esc(str) {
  if (typeof str !== 'string') return String(str ?? '');
  const el = document.createElement('span');
  el.textContent = str;
  return el.innerHTML;
}

function renderList(items) {
  if (!items || !items.length) return '';
  return '<ul>' + items.map(i => `<li>${esc(i)}</li>`).join('') + '</ul>';
}

function renderTable(headers, rows) {
  let html = '<table><thead><tr>';
  html += headers.map(h => `<th>${esc(h)}</th>`).join('');
  html += '</tr></thead><tbody>';
  for (const row of rows) {
    html += '<tr>' + row.map(c => `<td>${esc(c)}</td>`).join('') + '</tr>';
  }
  html += '</tbody></table>';
  return html;
}

function renderKV(obj) {
  if (!obj || typeof obj !== 'object') return '';
  let html = '<div class="kv-block">';
  for (const [k, v] of Object.entries(obj)) {
    const label = k.replace(/_/g, ' ');
    if (Array.isArray(v)) {
      html += `<div class="kv-row"><span class="kv-label">${esc(label)}</span>${renderList(v)}</div>`;
    } else {
      html += `<div class="kv-row"><span class="kv-label">${esc(label)}</span><span class="kv-value">${esc(v)}</span></div>`;
    }
  }
  html += '</div>';
  return html;
}

function renderCode(code, filename) {
  const label = filename ? `<div class="code-label">${esc(filename)}</div>` : '';
  return `${label}<pre><code>${esc(code)}</code></pre>`;
}


// ── Per-agent formatters ────────────────────────────────────────────

function formatResearch(d) {
  let html = '';
  const m = d.market_overview;
  if (m) {
    html += '<h4>Market Overview</h4>';
    html += `<div class="stat-row"><span class="stat-value">${esc(m.market_size)}</span></div>`;
    html += `<div class="stat-row"><span class="stat-value">${esc(m.growth_rate)}</span></div>`;
    if (m.key_segments) html += '<h5>Key Segments</h5>' + renderList(m.key_segments);
  }

  const aud = d.target_audience;
  if (aud) {
    html += '<h4>Target Audience</h4>';
    if (aud.primary) {
      html += `<h5>Primary: ${esc(aud.primary.segment)}</h5>`;
      html += renderList(aud.primary.pain_points);
      if (aud.primary.buying_behavior) html += `<p class="detail">${esc(aud.primary.buying_behavior)}</p>`;
    }
    if (aud.secondary) {
      html += `<h5>Secondary: ${esc(aud.secondary.segment)}</h5>`;
      html += renderList(aud.secondary.pain_points);
    }
  }

  if (d.trends) html += '<h4>Trends</h4>' + renderList(d.trends);
  if (d.risks) html += '<h4>Risks</h4>' + renderList(d.risks);
  return html;
}

function formatAnalysis(d) {
  let html = '';
  const comps = d.competitors;
  if (comps && comps.length) {
    html += '<h4>Competitors</h4>';
    html += renderTable(
      ['Name', 'Strengths', 'Weaknesses', 'Pricing', 'Share'],
      comps.map(c => [
        c.name || '',
        (c.strengths || []).join(', '),
        (c.weaknesses || []).join(', '),
        c.pricing || '',
        c.market_share || '',
      ])
    );
  }

  const swot = d.swot;
  if (swot) {
    html += '<h4>SWOT Analysis</h4><div class="swot-grid">';
    for (const key of ['strengths', 'weaknesses', 'opportunities', 'threats']) {
      html += `<div class="swot-cell"><h5>${key.charAt(0).toUpperCase() + key.slice(1)}</h5>${renderList(swot[key])}</div>`;
    }
    html += '</div>';
  }

  const pos = d.positioning;
  if (pos) {
    html += '<h4>Positioning</h4>';
    html += renderKV(pos);
  }
  return html;
}

function formatProduct(d) {
  let html = '';
  if (d.title) html += `<h4>${esc(d.title)}</h4>`;
  if (d.vision) html += `<p class="vision">${esc(d.vision)}</p>`;
  if (d.success_metrics) html += '<h5>Success Metrics</h5>' + renderList(d.success_metrics);

  const personas = d.user_personas;
  if (personas && personas.length) {
    html += '<h4>User Personas</h4>';
    for (const p of personas) {
      html += `<div class="persona"><h5>${esc(p.name)} &mdash; ${esc(p.role)}</h5>`;
      if (p.goals) html += '<span class="persona-label">Goals</span>' + renderList(p.goals);
      if (p.frustrations) html += '<span class="persona-label">Frustrations</span>' + renderList(p.frustrations);
      html += '</div>';
    }
  }

  const features = d.features;
  if (features) {
    if (features.mvp && features.mvp.length) {
      html += '<h4>MVP Features</h4>';
      html += renderTable(
        ['ID', 'Feature', 'Priority', 'Description'],
        features.mvp.map(f => [f.id || '', f.name || '', f.priority || '', f.description || ''])
      );
    }
    if (features.future && features.future.length) {
      html += '<h4>Future Features</h4>';
      html += renderTable(
        ['ID', 'Feature', 'Priority'],
        features.future.map(f => [f.id || '', f.name || '', f.priority || ''])
      );
    }
  }

  if (d.non_functional) html += '<h4>Non-Functional Requirements</h4>' + renderKV(d.non_functional);
  if (d.timeline) html += '<h4>Timeline</h4>' + renderKV(d.timeline);
  return html;
}

function formatArchitect(d) {
  let html = '';
  if (d.architecture_style) html += `<p class="stat-value">${esc(d.architecture_style)}</p>`;
  if (d.system_diagram) html += `<p class="detail">${esc(d.system_diagram)}</p>`;

  const tech = d.tech_stack;
  if (tech) {
    html += '<h4>Tech Stack</h4>';
    for (const [layer, items] of Object.entries(tech)) {
      html += `<h5>${esc(layer.replace(/_/g, ' '))}</h5>`;
      if (typeof items === 'object' && items !== null) {
        html += renderKV(items);
      } else {
        html += `<p>${esc(items)}</p>`;
      }
    }
  }

  if (d.services && d.services.length) {
    html += '<h4>Services</h4>';
    for (const s of d.services) {
      html += `<div class="service-card"><h5>${esc(s.name)}</h5>`;
      html += `<p class="detail">${esc(s.responsibility)}</p>`;
      html += `<p class="detail">${esc(s.tech)}</p>`;
      if (s.endpoints) html += renderList(s.endpoints);
      html += '</div>';
    }
  }

  if (d.data_model) {
    html += '<h4>Data Model</h4>';
    if (Array.isArray(d.data_model)) {
      html += renderTable(
        ['Entity', 'Fields'],
        d.data_model.map(e => [e.entity || e.name || '', (e.fields || []).join(', ')])
      );
    }
  }

  if (d.security) html += '<h4>Security</h4>' + renderKV(d.security);
  if (d.scalability) html += '<h4>Scalability</h4>' + renderKV(d.scalability);
  return html;
}

function formatCode(d) {
  let html = '';
  const structure = d.project_structure;
  if (Array.isArray(structure)) {
    html += '<h4>Project Structure</h4>' + renderList(structure);
  }

  for (const [section, label] of [['backend', 'Backend'], ['frontend', 'Frontend'], ['deployment', 'Deployment']]) {
    const files = d[section];
    if (files && typeof files === 'object') {
      html += `<h4>${label}</h4>`;
      for (const [filename, code] of Object.entries(files)) {
        if (typeof code === 'string' && code.length > 20) {
          html += renderCode(code.slice(0, 3000) + (code.length > 3000 ? '\n// ... truncated' : ''), filename);
        }
      }
    }
  }

  if (d.setup_instructions) html += '<h4>Setup Instructions</h4><ol>' + d.setup_instructions.map(s => `<li>${esc(s)}</li>`).join('') + '</ol>';
  return html;
}

function formatMarketing(d) {
  let html = '';
  const msg = d.messaging;
  if (msg) {
    html += '<h4>Messaging</h4>';
    if (msg.tagline) html += `<blockquote>${esc(msg.tagline)}</blockquote>`;
    if (msg.elevator_pitch) html += `<p>${esc(msg.elevator_pitch)}</p>`;
    if (msg.key_messages) html += renderList(msg.key_messages);
  }

  const launch = d.launch_plan;
  if (launch && launch.length) {
    html += '<h4>Launch Plan</h4>';
    for (const phase of launch) {
      html += `<div class="phase-card"><h5>${esc(phase.phase)}${phase.timeline ? ' &mdash; ' + esc(phase.timeline) : ''}</h5>`;
      if (phase.activities) html += '<span class="persona-label">Activities</span>' + renderList(phase.activities);
      if (phase.kpis) html += '<span class="persona-label">KPIs</span>' + renderList(phase.kpis);
      html += '</div>';
    }
  }

  const ch = d.channels;
  if (ch) {
    html += '<h4>Channels</h4>';
    for (const [type, items] of Object.entries(ch)) {
      if (Array.isArray(items)) html += `<h5>${esc(type.charAt(0).toUpperCase() + type.slice(1))}</h5>` + renderList(items);
    }
  }

  const pricing = d.pricing;
  if (pricing) {
    html += '<h4>Pricing</h4>';
    if (pricing.model) html += `<p class="detail">Model: ${esc(pricing.model)}</p>`;
    if (pricing.tiers && pricing.tiers.length) {
      html += renderTable(
        ['Tier', 'Price', 'Features'],
        pricing.tiers.map(t => [t.name || '', t.price || '', t.features || ''])
      );
    }
  }

  if (d.budget_allocation) html += '<h4>Budget Allocation</h4>' + renderKV(d.budget_allocation);
  return html;
}

function formatPitch(d) {
  let html = '';
  const slides = d.slides;
  if (slides && slides.length) {
    for (const s of slides) {
      html += `<div class="slide-card"><h4>Slide ${s.number || ''}: ${esc(s.title || '')}</h4>`;
      const content = s.content;
      if (content) {
        if (typeof content === 'string') {
          html += `<p>${esc(content)}</p>`;
        } else if (typeof content === 'object') {
          for (const [k, v] of Object.entries(content)) {
            const label = k.replace(/_/g, ' ');
            if (typeof v === 'string') {
              html += `<p class="detail"><strong>${esc(label)}</strong>: ${esc(v)}</p>`;
            } else if (Array.isArray(v)) {
              html += renderList(v.map(function(item) {
                return typeof item === 'object' ? JSON.stringify(item) : String(item);
              }));
            } else if (typeof v === 'object' && v !== null) {
              html += renderKV(v);
            }
          }
        }
      }
      // Also handle talking_points, notes, speaker_notes at slide level
      if (s.talking_points) html += '<p class="detail"><strong>Talking Points</strong></p>' + renderList(s.talking_points);
      if (s.notes) html += `<p class="detail"><em>${esc(s.notes)}</em></p>`;
      if (s.speaker_notes) html += `<p class="detail"><em>${esc(s.speaker_notes)}</em></p>`;
      html += '</div>';
    }
  }

  if (d.narrative_arc) html += `<h4>Narrative Arc</h4><p>${esc(d.narrative_arc)}</p>`;

  const faq = d.investor_faq;
  if (faq && faq.length) {
    html += '<h4>Investor FAQ</h4>';
    for (const item of faq) {
      html += `<details><summary>${esc(item.question || '')}</summary><p>${esc(item.answer || '')}</p></details>`;
    }
  }

  const proj = d.financial_projections;
  if (proj && typeof proj === 'object') {
    html += '<h4>Financial Projections</h4>';
    const years = Object.keys(proj);
    if (years.length) {
      const firstYear = proj[years[0]];
      if (firstYear && typeof firstYear === 'object') {
        const metrics = Object.keys(firstYear);
        html += renderTable(
          ['', ...years.map(y => y.replace(/_/g, ' '))],
          metrics.map(m => [m.charAt(0).toUpperCase() + m.slice(1), ...years.map(y => String(proj[y]?.[m] || ''))])
        );
      } else {
        html += renderKV(proj);
      }
    }
  }

  const ask = d.ask;
  if (ask) {
    html += '<h4>The Ask</h4>';
    if (ask.amount) html += `<div class="stat-row"><span class="stat-value">${esc(ask.amount)}</span></div>`;
    if (ask.use_of_funds) html += '<h5>Use of Funds</h5>' + renderKV(ask.use_of_funds);
    if (ask.milestones) html += '<h5>Milestones</h5>' + renderList(ask.milestones);
  }
  return html;
}

function formatDocument(d) {
  let html = '<div class="download-section">';
  html += '<h4>Your documents are ready</h4>';
  if (d.docx_id) {
    html += `<a href="/api/download/${esc(d.docx_id)}" class="download-btn" download>Download Word Document</a>`;
  }
  if (d.pptx_id) {
    html += `<a href="/api/download/${esc(d.pptx_id)}" class="download-btn" download>Download Pitch Deck</a>`;
  }
  html += '</div>';
  return html;
}


// ── Deep recursive renderer (no raw JSON ever) ─────────────────────

function renderDeep(value, depth) {
  if (depth === undefined) depth = 0;
  if (value === null || value === undefined) return '';
  if (typeof value === 'string') return `<p>${esc(value)}</p>`;
  if (typeof value === 'number' || typeof value === 'boolean') return `<p>${esc(String(value))}</p>`;

  if (Array.isArray(value)) {
    if (value.length === 0) return '';
    // Array of simple strings → bullet list
    if (value.every(function(v) { return typeof v === 'string' || typeof v === 'number'; })) {
      return renderList(value);
    }
    // Array of objects → render each
    let html = '';
    for (let i = 0; i < value.length; i++) {
      html += '<div class="deep-item">' + renderDeep(value[i], depth + 1) + '</div>';
    }
    return html;
  }

  if (typeof value === 'object') {
    let html = '';
    var keys = Object.keys(value);
    for (var k = 0; k < keys.length; k++) {
      var key = keys[k];
      var v = value[key];
      var label = key.replace(/_/g, ' ');
      label = label.charAt(0).toUpperCase() + label.slice(1);

      if (v === null || v === undefined || v === '') continue;

      if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') {
        html += '<div class="kv-row"><span class="kv-label">' + esc(label) + '</span><span class="kv-value">' + esc(String(v)) + '</span></div>';
      } else if (Array.isArray(v)) {
        if (depth < 3) html += '<h' + Math.min(depth + 4, 6) + '>' + esc(label) + '</h' + Math.min(depth + 4, 6) + '>';
        html += renderDeep(v, depth + 1);
      } else if (typeof v === 'object') {
        if (depth < 3) html += '<h' + Math.min(depth + 4, 6) + '>' + esc(label) + '</h' + Math.min(depth + 4, 6) + '>';
        html += renderDeep(v, depth + 1);
      }
    }
    return html || '<p class="detail">No data</p>';
  }

  return '<p>' + esc(String(value)) + '</p>';
}


// ── Main dispatcher ─────────────────────────────────────────────────

function formatAgentOutput(agentName, data) {
  if (!data || typeof data !== 'object') return renderDeep(data);
  if (data.raw_output) return '<div class="formatted-prose">' + esc(data.raw_output).replace(/\n/g, '<br>') + '</div>';

  try {
    const formatters = {
      ResearchAgent:  formatResearch,
      AnalysisAgent:  formatAnalysis,
      ProductAgent:   formatProduct,
      ArchitectAgent: formatArchitect,
      CodeAgent:      formatCode,
      MarketingAgent: formatMarketing,
      PitchAgent:     formatPitch,
      DocumentAgent:  formatDocument,
    };
    const fn = formatters[agentName];
    if (fn) {
      const result = fn(data);
      if (result) return result;
    }
  } catch (e) {
    console.warn('Format error for', agentName, e);
  }
  // Fallback: render structured HTML, never raw JSON
  return renderDeep(data);
}
