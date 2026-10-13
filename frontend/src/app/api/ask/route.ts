export function GET() {}
export async function POST(request: Request) {
  const body = await request.json();
  const response = await fetch('http://127.0.0.1:5000/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  return Response.json(data, { status: response.status });
}
