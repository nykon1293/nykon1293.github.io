console.log(JSON.stringify((() => {
  const vw = document.documentElement.clientWidth;
  const sw = document.documentElement.scrollWidth;
  const bodySW = document.body.scrollWidth;
  const h1 = document.querySelector('h1');
  const muted = document.querySelector('.lead, p');
  const cs = (el) => el ? getComputedStyle(el) : null;
  const ratio = (fg, bg) => {
    const lum = (c) => {
      const m = c.match(/rgba?\(([^)]+)\)/);
      if (!m) return null;
      const p = m[1].split(',').map(x=>parseFloat(x.trim()));
      const [r,g,b,a=1] = p.length===4?p:[...p,1];
      const f = (v) => { v/=255; return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4); };
      return .2126*f(r)+.7152*f(g)+.0722*f(b);
    };
    const L1 = lum(fg), L2 = lum(bg);
    if (L1==null||L2==null) return null;
    const hi=Math.max(L1,L2), lo=Math.min(L1,L2);
    return (hi+.05)/(lo+.05);
  };
  const bodyBg = cs(document.body).backgroundColor;
  const lead = document.querySelector('.lead');
  let leadRatio = null;
  if (lead) leadRatio = ratio(cs(lead).color, bodyBg);
  return {vw, sw, bodySW, overflow: sw>vw+2||bodySW>vw+2, leadColor: lead?cs(lead).color:null, bodyBg, leadRatio};
})()))