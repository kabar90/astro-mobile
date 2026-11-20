import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const failures = new Rate('catalogue_failures');
const productsLatency = new Trend('products_latency');
const categoriesLatency = new Trend('categories_latency');

const baseUrl = (__ENV.SUPABASE_URL || '').replace(/\/$/, '');
const anonKey = __ENV.SUPABASE_ANON_KEY || '';
const targetVus = Number(__ENV.TARGET_VUS || 200);
const headers = {
  apikey: anonKey,
  Authorization: `Bearer ${anonKey}`,
  Accept: 'application/json',
};

export const options = {
  discardResponseBodies: true,
  stages: [
    { duration: '10s', target: targetVus },
    { duration: '20s', target: targetVus },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],
    catalogue_failures: ['rate<0.01'],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)'],
};

export default function () {
  // One app-launch catalogue fetch per virtual user, with users ramping
  // gradually over 10 seconds instead of arriving as one instant burst.
  const products = http.get(
    `${baseUrl}/rest/v1/products?select=id,name,price,category,stock,image_url,colors,subcategory_id,reward_points,allow_points_payment&is_active=eq.true&order=created_at.desc&limit=100`,
    { headers, tags: { endpoint: 'products' } }
  );
  productsLatency.add(products.timings.duration);
  const productsOk = check(products, {
    'products returns HTTP 200': (r) => r.status === 200,
  });
  failures.add(!productsOk);

  const categories = http.get(
    `${baseUrl}/rest/v1/categories?select=id,name,sort_order,parent_id,image_url&is_active=eq.true&order=sort_order.asc`,
    { headers, tags: { endpoint: 'categories' } }
  );
  categoriesLatency.add(categories.timings.duration);
  const categoriesOk = check(categories, {
    'categories returns HTTP 200': (r) => r.status === 200,
  });
  failures.add(!categoriesOk);

  // Keep each virtual user active for the test window without polling or writes.
  sleep(30);
}
