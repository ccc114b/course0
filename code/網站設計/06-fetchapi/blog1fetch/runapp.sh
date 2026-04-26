 lsof -ti :3001 | xargs kill -9 2>/dev/null || echo "No process on port 3001"
 npm start
 