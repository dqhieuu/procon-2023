const matchIdx = Array(500)
  .fill("")
  .map((_, i) => i);

const data = matchIdx.map(
  async (idx) =>
    [
      await fetch(
        `https://procon2023.duckdns.org/api/player/games/${idx}/actions`,
        {
          headers: {
            authorization:
              "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MjYsIm5hbWUiOiJDVFUgQWRtaW4iLCJpc19hZG1pbiI6dHJ1ZSwiaWF0IjoxNjk5OTYxMjQyLCJleHAiOjE3MDAxMzQwNDJ9.pyjaQrAwtShslCx4_6e74IkP2_9hBmT7s1ITaQlRrJQ",
          },
        }
      ).then((a) => a.json()),
    ].map((r) => (r?.detail ? null : r))[0]
);

const resolved = await Promise.all(data);

const objOfIdx = resolved.reduce((acc, cur, idx) => {
  if (!cur) return acc;

  acc[idx] = cur;
  return acc;
}, {});

const processed = Object.entries(objOfIdx).reduce((acc, [idx, cur]) => {
  if (cur.length === 0) return acc;

  acc[idx] = JSON.stringify(cur);
  return acc;
}, {});

console.log(processed);
