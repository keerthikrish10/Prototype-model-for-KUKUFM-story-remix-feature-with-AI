async function applyRemix(storyId, modifications) {
  const response = await fetch('/api/remix', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ story_id: storyId, modifications })
  });
  
  const data = await response.json();
  return data.content;
}

// Example usage:
const happyEndingRemix = await applyRemix('story_001', {
  genre: 'mystery',
  ending: 'happy',
  tone: 'uplifting'
});