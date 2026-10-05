// Requires seeded synthetic Django on :8000 and Vite with VITE_DEMO_MODE=false on :5174.
import { chromium, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
const browser=await chromium.launch();
await mkdir('test-results/role-dashboards',{recursive:true});
try {
  for (const [username,heading] of [['asha','My recent updates'],['meera','Team updates grouped by team'],['admin','Account status'],['security','Audit-event timeline']]) {
    const context=await browser.newContext({reducedMotion:'reduce'});
    const page=await context.newPage();
    const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('response',r=>{if(r.url().includes('/api/') && r.status()>=500)errors.push(`${r.status()} ${r.url()}`);});
    await page.goto('http://127.0.0.1:5174/api/v1/auth/login');
    await page.getByLabel('Username').fill(username);
    await page.getByLabel('Password',{exact:true}).fill(process.env.SMOKE_PASSWORD || 'Synthetic-pilot-2026!');
    await page.getByRole('button',{name:'Continue to workspace'}).click();
    await expect(page.getByRole('heading',{name:heading,exact:true})).toBeVisible({timeout:30000});
    await expect(page.locator('.dashboard-stats .stat-card')).toHaveCount(4);
    const titleByUser={asha:'Employee dashboard',meera:'Team lead dashboard',admin:'Organization admin dashboard',security:'Security dashboard'};
    await expect(page.getByRole('heading',{name:titleByUser[username],exact:true})).toBeVisible();
    if(username==='asha') {
      await page.getByRole('link',{name:'Upload to assigned project',exact:true}).click();
      await expect(page.getByRole('dialog')).toBeVisible();
      await page.getByRole('button',{name:'Cancel',exact:true}).click();
      await page.goto('http://127.0.0.1:5174');
      await expect(page.getByRole('heading',{name:heading,exact:true})).toBeVisible();
      const denied=await context.request.get('http://127.0.0.1:5174/api/v1/dashboard?view=admin');
      expect(denied.status()).toBe(404);
    }
    if(username==='security') {
      await page.getByLabel('Event type').selectOption('denials');
      await expect(page.getByRole('heading',{name:heading,exact:true})).toBeVisible();
      await expect(page.getByRole('heading',{name:'Security settings',exact:true})).toBeVisible();
    }
    if(username==='meera') {
      await page.getByRole('link',{name:'Create update',exact:true}).click();
      await expect(page.getByRole('button',{name:'Save private draft',exact:true})).toBeEnabled();
      await expect(page.getByRole('checkbox',{name:'Blocked / needs help',exact:true})).toBeVisible();
      await page.getByRole('button',{name:'Cancel',exact:true}).click();
      await page.goto('http://127.0.0.1:5174');
      await expect(page.getByRole('heading',{name:heading,exact:true})).toBeVisible();
    }
    if(username==='admin') {
      await page.getByRole('link',{name:'Invite user',exact:true}).click();
      await expect(page.getByRole('dialog')).toBeVisible();
      await page.getByRole('button',{name:'Cancel',exact:true}).click();
      await page.goto('http://127.0.0.1:5174');
      await expect(page.getByRole('heading',{name:heading,exact:true})).toBeVisible();
    }
    for (const [label,width,height] of [['desktop',1440,1000],['mobile',390,844]]) {
      await page.setViewportSize({width,height});
      if(label==='mobile') await expect(page.getByRole('navigation',{name:'Main navigation'})).toHaveCount(0);
      await page.screenshot({path:`test-results/role-dashboards/${username}-${label}.png`,fullPage:true,animations:'disabled'});
      expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
    }
    if(username!=='asha') {
      await page.getByRole('button',{name:'Personal workspace',exact:true}).click();
      await expect(page.getByRole('heading',{name:'My recent updates',exact:true})).toBeVisible();
      if(username==='admin') {
        await page.getByRole('button',{name:'Open organization admin dashboard',exact:true}).click();
        await expect(page.getByRole('heading',{name:'Organization admin dashboard',exact:true})).toBeVisible();
      }
    }
    expect(errors).toEqual([]);
    await context.close();
    console.log(`${username}: role dashboard, quick actions, responsive layout and access checks passed`);
  }
} finally {await browser.close();}
