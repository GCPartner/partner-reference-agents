const http = require('http');
http.get('http://localhost:8000/openapi.json', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    const schema = JSON.parse(data);
    console.log(JSON.stringify(schema.components.schemas['Content-Input'], null, 2));
  });
});
