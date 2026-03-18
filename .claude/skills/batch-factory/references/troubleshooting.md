# Batch Factory Troubleshooting Guide

This document provides solutions to common issues when using the batch-factory skill.

## Common Issues

### Issue 1: No Materials Collected

**Symptoms:**
- Material pool is empty
- Error: "未找到素材池"
- No materials in Notion database

**Possible Causes:**
1. Network connectivity issues
2. API rate limits exceeded
3. Invalid source configuration
4. API keys missing or expired

**Solutions:**

**Check network connection:**
```bash
ping google.com
curl -I https://news.ycombinator.com
```

**Verify API keys:**
```bash
# Check .env file
cat .env | grep -E "(TAVILY|YOUTUBE|NOTION)_API"

# Test Tavily API
curl -X POST https://api.tavily.com/search \
  -H "Content-Type: application/json" \
  -d '{"api_key":"YOUR_KEY","query":"test"}'
```

**Check source configuration:**
```bash
cat src/config/sources.yaml
```

**Verify sources are enabled:**
- Open `src/config/sources.yaml`
- Ensure sources are not commented out
- Check RSS feed URLs are valid

### Issue 2: Topic Planning Fails

**Symptoms:**
- No topics recommended
- Error: "plan_result 中没有可选素材"
- Empty recommended_topics in pipeline state

**Possible Causes:**
1. Insufficient materials for direction
2. AI API failure (Gemini)
3. Materials don't match direction filters
4. Scoring threshold too high

**Solutions:**

**Check material count:**
```bash
# View material pool
cat content/pool/$(ls -t content/pool/*.json | head -1) | jq '.dedup_total'

# Check materials by category
cat content/pool/$(ls -t content/pool/*.json | head -1) | jq '.items[] | .category' | sort | uniq -c
```

**Verify Gemini API:**
```bash
# Check API key
echo $GEMINI_API_KEY

# Test API
curl "https://generativelanguage.googleapis.com/v1/models?key=$GEMINI_API_KEY"
```

**Lower direction filters:**
- Edit `src/collector/directions.py`
- Add more categories to direction filters
- Adjust TRENDING_KEYWORDS

**Check AI recommendation:**
```bash
# Run planner manually
python src/collector/planner.py --pool content/pool/latest.json --recommend
```

### Issue 3: Article Generation Fails

**Symptoms:**
- Draft file not created
- Error during write stage
- Empty draft content

**Possible Causes:**
1. Invalid topic title
2. AI API failure
3. Source URLs inaccessible
4. Insufficient context

**Solutions:**

**Verify topic:**
```bash
# Check selected topic in pipeline state
cat content/pipeline/$(ls -t content/pipeline/*.json | head -1) | jq '.selected_topic'
```

**Test article generation manually:**
```bash
python src/generator/main.py "Test Topic Title"
```

**Check source URLs:**
```bash
# Extract source URLs from pipeline state
cat content/pipeline/$(ls -t content/pipeline/*.json | head -1) | jq '.selected_sources[]'

# Test URL accessibility
curl -I "https://example.com/article"
```

**Increase AI timeout:**
- Edit `src/generator/gemini_client.py`
- Increase timeout parameter

### Issue 4: AI Review Always Fails

**Symptoms:**
- Review score always < 70
- Articles keep getting rewritten
- Max retries exceeded

**Possible Causes:**
1. Review criteria too strict
2. Generated content quality issues
3. AI reviewer misconfigured
4. Wrong scoring model

**Solutions:**

**Check review scores:**
```bash
# View review feedback
cat content/pipeline/$(ls -t content/pipeline/*.json | head -1) | jq '.review_feedback'
```

**Lower pass threshold:**
- Edit `src/reviewer/quality_checker.py`
- Change `PASS_THRESHOLD = 70` to lower value (e.g., 60)

**Review manually:**
```bash
# Run reviewer on draft
python src/reviewer/quality_checker.py content/drafts/your-article.md
```

**Check scoring dimensions:**
- Edit `src/reviewer/quality_checker.py`
- Review scoring criteria
- Adjust weights if needed

### Issue 5: Publishing Fails

**Symptoms:**
- Publish status: "failed"
- Platform-specific errors
- Credentials expired

**Possible Causes:**
1. Platform credentials expired
2. Network issues
3. Platform rate limits
4. Content violates platform rules
5. Cookie/token expired

**Solutions:**

**Check platform credentials:**
```bash
# Xiaohongshu
echo $XIAOHONGSHU_COOKIE

# Zhihu
echo $ZHIHU_COOKIE

# Verify cookies are not expired
```

**Test platform manually:**
```bash
# Publish single article
python src/publisher/main.py content/drafts/test.md --platforms xiaohongshu
```

**Update credentials:**
1. Login to platform in browser
2. Export cookies using browser extension
3. Update `.env` file with new cookies
4. Restart pipeline

**Check platform status:**
- Visit platform website
- Verify account is not banned/restricted
- Check for maintenance notices

**Review content:**
- Check for sensitive keywords
- Verify images are appropriate
- Ensure content meets platform guidelines

### Issue 6: Batch Execution Hangs

**Symptoms:**
- Process stops responding
- No progress for long time
- CPU/memory usage high

**Possible Causes:**
1. Network timeout
2. API rate limit
3. Memory exhaustion
4. Infinite retry loop

**Solutions:**

**Check process status:**
```bash
# Find Python process
ps aux | grep batch_pipeline

# Check resource usage
top -p <PID>
```

**Kill and restart:**
```bash
# Kill process
pkill -f batch_pipeline

# Restart with lower count
python src/pipeline/batch_pipeline.py --count 1
```

**Check logs:**
```bash
# View latest pipeline states
ls -lt content/pipeline/*.json | head -5

# Check for errors
cat content/pipeline/$(ls -t content/pipeline/*.json | head -1) | jq '.error'
```

**Reduce batch size:**
- Use `--count 1` for testing
- Gradually increase count
- Monitor resource usage

### Issue 7: Notion Sync Fails

**Symptoms:**
- Data not appearing in Notion
- Error: "Notion API 失败"
- notion_saved: 0

**Possible Causes:**
1. Notion API key invalid
2. Database IDs incorrect
3. Permission issues
4. API rate limit

**Solutions:**

**Verify Notion credentials:**
```bash
# Check API key
echo $NOTION_API_KEY

# Check database IDs
echo $NOTION_DATABASE_ID
echo $NOTION_TOPICS_DB_ID
echo $NOTION_DRAFTS_DB_ID
echo $NOTION_PUBLISH_DB_ID
```

**Test Notion API:**
```bash
curl -X GET https://api.notion.com/v1/databases/$NOTION_DATABASE_ID \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2022-06-28"
```

**Check permissions:**
- Open Notion workspace
- Verify integration has access to databases
- Check database sharing settings

**Recreate databases:**
```bash
# Run setup script
python scripts/create_notion_databases.py
python scripts/setup_notion_databases.py
```

## Performance Issues

### Slow Execution

**Symptoms:**
- Batch takes > 1 hour
- Each article takes > 10 minutes

**Solutions:**

**Use --no-cards:**
```bash
python src/pipeline/batch_pipeline.py --no-cards
```

**Reduce article count:**
```bash
python src/pipeline/batch_pipeline.py --count 1
```

**Single platform:**
```bash
python src/pipeline/batch_pipeline.py --platforms xiaohongshu
```

**Check network speed:**
```bash
speedtest-cli
```

### High Memory Usage

**Symptoms:**
- Memory usage > 2GB
- System becomes slow
- Out of memory errors

**Solutions:**

**Monitor memory:**
```bash
# Check memory usage
free -h

# Monitor process
top -p $(pgrep -f batch_pipeline)
```

**Reduce batch size:**
- Use `--count 1`
- Process articles sequentially
- Clear cache between runs

**Increase swap:**
```bash
# Check swap
swapon --show

# Add swap if needed
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Debug Commands

### View Latest Results

```bash
# Latest batch results
cat content/batch/$(ls -t content/batch/*.json | head -1) | jq '.'

# Latest pipeline state
cat content/pipeline/$(ls -t content/pipeline/*.json | head -1) | jq '.'

# Latest material pool
cat content/pool/$(ls -t content/pool/*.json | head -1) | jq '.dedup_total'
```

### Check File Counts

```bash
# Count drafts
ls content/drafts/*.md | wc -l

# Count pipeline states
ls content/pipeline/*.json | wc -l

# Count batch results
ls content/batch/*.json | wc -l
```

### Verify Configuration

```bash
# Check publishers config
cat src/config/publishers.yaml

# Check sources config
cat src/config/sources.yaml

# Check environment variables
env | grep -E "(NOTION|GEMINI|XIAOHONGSHU|ZHIHU)"
```

### Clean Up

```bash
# Remove old pipeline states (keep last 10)
ls -t content/pipeline/*.json | tail -n +11 | xargs rm -f

# Remove old batch results (keep last 5)
ls -t content/batch/*.json | tail -n +6 | xargs rm -f

# Clean up failed drafts
find content/drafts -name "*.md" -size 0 -delete
```

## Getting Help

If issues persist:

1. **Check logs:** Review pipeline state files for detailed error messages
2. **Test components:** Run individual stages manually to isolate issues
3. **Verify setup:** Ensure all prerequisites are configured correctly
4. **Reduce scope:** Start with minimal configuration and gradually expand
5. **Report issues:** Document error messages and steps to reproduce

## Prevention Tips

1. **Test first:** Always run with `--count 1` before large batches
2. **Monitor resources:** Watch CPU/memory usage during execution
3. **Verify credentials:** Check API keys and cookies before starting
4. **Backup data:** Keep copies of important pipeline states
5. **Update regularly:** Keep dependencies and API clients up to date
