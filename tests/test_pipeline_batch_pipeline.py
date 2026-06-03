"""test_pipeline_batch_pipeline.py — batch pipeline defaults."""

from pipeline.batch_pipeline import BatchPipeline


def test_batch_pipeline_default_platforms_only_dongchedi():
    batch = BatchPipeline()

    assert batch.platforms == "dongchedi"
