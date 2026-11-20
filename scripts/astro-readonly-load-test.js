import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const failures = new Rate('catalogue_failures');
const productsLatency = new Trend('products_latency');
const categoriesLatency = new Trend('categories_latency');

const baseUrl = (__ENV.SUPABASE_URL || '').replace(/\\/$/, '');
const anonKey = __ENV.SUPABASE_ANON_KEY || '';
const headers = {
  apikey: anonKey,
  Authorization: `Bearer ${anonKey}`,
  Accept: 'application/json',
};

export const options = {
  discardResponseBodies: true,
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1500'],
    catalogue_failures: ['rate<0.01'],
    products_latency: ['p(95)<1500'],
    categories_latency: ['p(95)<1500'],
  },
};

export default function () {
  // Match the app's optimized catalogue request: descriptions load on demand.
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

  sleep(1.5);
}
