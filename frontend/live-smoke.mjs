import { chromium } from '@playwright/test';

const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => {
    if (response.url().includes('/api/') && response.status() >= 500)
      errors.push(`${response.status()} ${response.url()}`);
  });
  await page.goto('http://127.0.0.1:5174');
  await page.getByRole('button', {name:'Continue with organization SSO'}).click();
  await page.getByLabel('Username').fill('asha');
  await page.getByLabel('Password', {exact:true}).fill(process.env.SMOKE_PASSWORD || 'Synthetic-pilot-2026!');
  await page.getByRole('button', {name:'Continue to workspace'}).click();
  await page.getByRole('heading', {name:'Welcome back, Asha'}).waitFor();
  for (const route of ['/projects', '/work', '/documents', '/people', '/settings', '/search', '/notifications']) {
    await page.goto(`http://127.0.0.1:5174${route}`);
    await page.waitForLoadState('networkidle');
    if (await page.getByText('Unable to load this page', {exact:true}).count()) errors.push(`Failed page ${route}`);
  }
  await page.goto('http://127.0.0.1:5174/assistant');
  await page.getByPlaceholder('Ask a question about your workspace…').fill('What is the Atlas launch overview?');
  await page.getByRole('button', {name:'Send question'}).click();
  await page.waitForURL('**/assistant/*');
  await page.waitForLoadState('networkidle');
  if (errors.length) throw new Error(errors.join('\n'));
  console.log('Live smoke passed: CSRF login, seven feature pages, assistant request, no server errors.');
} finally {
  await browser.close();
}
