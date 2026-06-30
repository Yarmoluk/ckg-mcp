#!/usr/bin/env node
// Run: STRIPE_SECRET_KEY=sk_live_xxx node stripe-setup.js
// Creates the ckg-mcp Pro product + price + payment link, prints the payment link URL.

const key = process.env.STRIPE_SECRET_KEY;
if (!key) { console.error('Set STRIPE_SECRET_KEY env var'); process.exit(1); }

const stripe = async (method, path, body) => {
  const res = await fetch(`https://api.stripe.com/v1${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${key}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: body ? new URLSearchParams(body).toString() : undefined,
  });
  const data = await res.json();
  if (data.error) throw new Error(`Stripe error: ${data.error.message}`);
  return data;
};

(async () => {
  console.log('Creating ckg-mcp Pro product...');
  const product = await stripe('POST', '/products', {
    name: 'ckg-mcp Pro',
    description: 'Unlock all 85 CKG domains — healthcare, enterprise data, AI infrastructure. Works with Claude, GPT-4o, Gemini, Llama, and any MCP-compatible agent.',
    'metadata[tier]': 'pro',
    'metadata[domains]': '85',
  });
  console.log(`  Product: ${product.id}`);

  const price = await stripe('POST', '/prices', {
    product: product.id,
    unit_amount: 2000,
    currency: 'usd',
    'recurring[interval]': 'month',
    'nickname': 'ckg-mcp Pro Monthly',
  });
  console.log(`  Price:   ${price.id}`);

  const link = await stripe('POST', '/payment_links', {
    'line_items[0][price]': price.id,
    'line_items[0][quantity]': 1,
    'after_completion[type]': 'redirect',
    'after_completion[redirect][url]': 'https://graphifymd.com/pro/success.html',
    'allow_promotion_codes': 'true',
    'billing_address_collection': 'auto',
    'metadata[product]': 'ckg-mcp-pro',
  });

  console.log('\n✓ Done. Add this to pro/index.html:\n');
  console.log(`  STRIPE_PAYMENT_LINK_URL = '${link.url}'`);
  console.log('\n  Add this webhook endpoint in Stripe Dashboard → Webhooks:');
  console.log('  URL: https://graphifymd.com/api/stripe-webhook');
  console.log('  Events: checkout.session.completed, customer.subscription.deleted, invoice.payment_failed');
  console.log('\n  Then add these Vercel env vars:');
  console.log('    STRIPE_SECRET_KEY=' + key);
  console.log('    STRIPE_WEBHOOK_SECRET=<from Stripe webhook page>');
  console.log('    KV_REST_API_URL=<from Vercel KV>');
  console.log('    KV_REST_API_TOKEN=<from Vercel KV>');
})();
