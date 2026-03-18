# Batch Factory Workflow Details

This document provides detailed workflow documentation for the batch-factory skill.

## Complete Workflow

### Stage 1: Material Search

**Execution:** Once per batch

**Process:**
1. Collect materials from configured sources (RSS, HN, GitHub, Tavily, YouTube)
2. Call normalizer for deduplication and clustering
3. Generate material pool JSON
4. Sync to Notion material database (status: pending)

**Output:**
- File: `content/pool/YYYY-MM-DD-pool.json`
- Notion: Materials synced with "pending" status

**Configuration:**
- Sources: `src/config/sources.yaml`
- Notion: `NOTION_DATABASE_ID` in `.env`

### Stage 2: Topic Planning

**Execution:** Once per batch (both directions)

**Process:**

**AI Technology Direction:**
1. Filter materials by category (AI, ML, Tech)
2. Score each material (timeliness, popularity, quality)
3. Sort by score
4. AI analyzes top 10 materials
5. Recommend 3-5 topics
6. Sync to Notion topics database

**Automotive Direction:**
1. Filter materials by category (Auto, EV, Transport)
2. Score each material
3. Sort by score
4. AI analyzes top 10 materials
5. Recommend 3-5 topics
6. Sync to Notion topics database

**Output:**
- Recommended topics saved in pipeline state
- Notion: Topics synced with "pending" status

**AI Recommendation Prompt:**
```
You are a senior content strategist. Here are the top 10 materials for [direction]:

[materials summary]

Please analyze these materials and recommend 3-5 topics worth writing about.
Each topic should include:
1. Topic title (suggested article title, attractive)
2. Recommendation reason (why worth writing, timeliness, topic heat)
3. Suggested angle (entry point, differentiation direction)
4. Related materials (which materials can be referenced, marked by number)
```

### Stage 3: Batch Generation

**Execution:** N times per direction (N = --count parameter)

**Process for each article:**

1. **Select Topic**
   - Take next topic from recommended list
   - Set as selected_topic in pipeline state

2. **Generate Content**
   - Call `generator.writer.generate_article()`
   - Auto-complete frontmatter (title, date, tags, summary)
   - Save to `content/drafts/`

3. **Generate Visual Cards** (if --no-cards not set)
   - Call `card_generator.generate_cards()`
   - Generate HTML with visual design
   - Save to `content/drafts/`

4. **AI Quality Review**
   - Read draft content
   - AI scores 6 dimensions (total 100 points)
   - Pass threshold: ≥70 points
   - If fail: auto-rewrite (max 3 retries)

5. **Sync to Notion**
   - Save draft to Notion drafts database
   - Status: "pending review" or "approved"
   - Link to related topics

**Output per article:**
- Draft: `content/drafts/<slug>.md`
- Cards: `content/drafts/<slug>-cards.html`
- Pipeline state: `content/pipeline/<pipeline_id>.json`

### Stage 4: Multi-Platform Publishing

**Execution:** Once per article, per platform

**Process:**

1. **Load Draft Package**
   - Read markdown file
   - Parse frontmatter
   - Extract content and metadata

2. **Build Publish Packages**
   - For each platform:
     - Call `packager.build_publish_package()`
     - Handle image upload
     - Format conversion (markdown → platform format)
     - Generate platform-specific package

3. **Execute Publishing**
   - For each platform:
     - Get publisher from registry
     - Call `publisher.publish(package)`
     - Record result (success/failure)

4. **Record Results**
   - Save to Notion publish records database
   - Update draft status to "published"
   - Link to publish records

**Output:**
- Notion: Publish records with platform links
- Pipeline state: publish_results array

## Parameter Combinations

### Common Scenarios

**Scenario 1: Default batch production**
```bash
python src/pipeline/batch_pipeline.py
```
- Articles: 4 (2 AI + 2 automotive)
- Platforms: xiaohongshu, zhihu
- Publications: 8

**Scenario 2: Large batch**
```bash
python src/pipeline/batch_pipeline.py --count 5
```
- Articles: 10 (5 AI + 5 automotive)
- Platforms: xiaohongshu, zhihu
- Publications: 20

**Scenario 3: Single platform**
```bash
python src/pipeline/batch_pipeline.py --platforms xiaohongshu
```
- Articles: 4 (2 AI + 2 automotive)
- Platforms: xiaohongshu only
- Publications: 4

**Scenario 4: Custom sources**
```bash
python src/pipeline/batch_pipeline.py --sources hn,github
```
- Only collect from HN and GitHub
- Articles: 4 (2 AI + 2 automotive)
- Platforms: xiaohongshu, zhihu
- Publications: 8

**Scenario 5: No visual cards**
```bash
python src/pipeline/batch_pipeline.py --no-cards
```
- Skip card generation (faster)
- Articles: 4 (2 AI + 2 automotive)
- Platforms: xiaohongshu, zhihu
- Publications: 8

### Parameter Conflicts

**None currently** - All parameters are independent and can be combined freely.

## Error Handling

### Material Search Failures

**Symptom:** No materials collected

**Possible causes:**
- Network issues
- API rate limits
- Invalid source configuration

**Recovery:**
- Check network connection
- Verify API keys in `.env`
- Check `src/config/sources.yaml`

### Topic Planning Failures

**Symptom:** No topics recommended

**Possible causes:**
- Empty material pool
- AI API failure
- Insufficient materials for direction

**Recovery:**
- Check material pool file exists
- Verify Gemini API key
- Try different direction

### Generation Failures

**Symptom:** Article generation fails

**Possible causes:**
- AI API failure
- Invalid topic
- Insufficient source materials

**Recovery:**
- Check Gemini API key
- Verify topic is valid
- Check source URLs are accessible

### Review Failures

**Symptom:** Review always fails

**Possible causes:**
- Review criteria too strict
- AI API issues
- Content quality issues

**Recovery:**
- Check review threshold (default 70)
- Verify Gemini API key
- Review generated content manually

### Publishing Failures

**Symptom:** Publishing fails for specific platform

**Possible causes:**
- Platform credentials expired
- Network issues
- Platform rate limits
- Content violates platform rules

**Recovery:**
- Check platform credentials in `.env`
- Verify network connection
- Check platform rate limits
- Review content for violations

## Performance Optimization

### Tips for Faster Execution

1. **Use --no-cards** - Skip visual card generation
2. **Reduce --count** - Generate fewer articles
3. **Single platform** - Publish to one platform only
4. **Parallel execution** - Future enhancement (not yet implemented)

### Resource Usage

**Memory:**
- Material search: ~500MB
- Topic planning: ~200MB per direction
- Article generation: ~300MB per article
- Publishing: ~100MB per platform

**Disk:**
- Material pool: ~1-5MB
- Draft files: ~10-50KB per article
- Visual cards: ~50-200KB per article
- Pipeline states: ~5-20KB per article

**Network:**
- Material collection: ~10-50MB
- AI API calls: ~1-5MB per article
- Image uploads: ~1-10MB per article
- Platform publishing: ~100KB-1MB per article

## Monitoring and Debugging

### Log Files

**Pipeline states:**
- Location: `content/pipeline/<pipeline_id>.json`
- Contains: Complete execution history
- Use: Debug individual article issues

**Batch results:**
- Location: `content/batch/<timestamp>-batch.json`
- Contains: Summary of all articles
- Use: Overview of batch execution

### Status Checking

**During execution:**
- Watch console output for progress
- Check `content/drafts/` for generated files
- Monitor `content/pipeline/` for state files

**After execution:**
- Read batch results JSON
- Check Notion databases for synced data
- Verify platform publications

### Common Debug Commands

```bash
# Check latest pipeline state
cat content/pipeline/$(ls -t content/pipeline/*.json | head -1)

# Check latest batch results
cat content/batch/$(ls -t content/batch/*.json | head -1)

# List generated drafts
ls -lh content/drafts/*.md

# Check material pool
cat content/pool/$(ls -t content/pool/*.json | head -1) | jq '.dedup_total'
```
