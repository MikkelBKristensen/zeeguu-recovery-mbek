# Reflexion Model — Zeeguu-API

| From | To | Verdict | Evidence |
|------|----|---------|----------|
| api | audio-lessons | **CONVERGENCE** | `api.endpoints` -> `core.audio_lessons` |
| api | content-pipeline | **CONVERGENCE** | `api.endpoints` -> `core.content_recommender`; `api.endpoints` -> `core.content_retriever` |
| api | data-layer | **CONVERGENCE** | `api.endpoints` -> `core.model`; `api.utils` -> `core.model` |
| api | language-processing | **CONVERGENCE** | `api.endpoints` -> `core.crowd_translations`; `api.endpoints` -> `core.language` (+4 more) |
| api | learning-system | **CONVERGENCE** | `api.endpoints` -> `core.behavioral_modeling`; `api.endpoints` -> `core.bookmark_operations` (+3 more) |
| api | operations | **ABSENCE** | (none) |
| api | other | **CONVERGENCE** | `api.endpoints` -> `core.util`; `api.endpoints` -> `core.verbal_flashcards` |
| api | user-management | **CONVERGENCE** | `api.endpoints` -> `core.account_management`; `api.endpoints` -> `core.emailer` (+4 more) |
| audio-lessons | data-layer | **CONVERGENCE** | `core.audio_lessons` -> `core.model` |
| audio-lessons | language-processing | **CONVERGENCE** | `core.audio_lessons` -> `core.llm_services` |
| audio-lessons | learning-system | **CONVERGENCE** | `core.audio_lessons` -> `core.word_scheduling` |
| audio-lessons | other | **ABSENCE** | (none) |
| audio-lessons | user-management | **DIVERGENCE** | `core.audio_lessons` -> `core.emailer` |
| content-pipeline | data-layer | **CONVERGENCE** | `core.content_cleaning` -> `core.model`; `core.content_quality` -> `core.model` (+3 more) |
| content-pipeline | language-processing | **CONVERGENCE** | `core.content_quality` -> `core.ml_models`; `core.content_retriever` -> `core.llm_services` (+2 more) |
| content-pipeline | other | **CONVERGENCE** | `core.content_recommender` -> `core.util`; `core.feed_handler` -> `core.util` (+1 more) |
| data-layer | api | **DIVERGENCE** | `core.model` -> `api.utils` |
| data-layer | audio-lessons | **DIVERGENCE** | `core.model` -> `core.audio_lessons` |
| data-layer | content-pipeline | **DIVERGENCE** | `core.model` -> `core.content_cleaning`; `core.model` -> `core.content_quality` (+4 more) |
| data-layer | language-processing | **DIVERGENCE** | `core.model` -> `core.language`; `core.model` -> `core.llm_services` (+3 more) |
| data-layer | learning-system | **DIVERGENCE** | `core.model` -> `core.behavioral_modeling`; `core.model` -> `core.bookmark_quality` (+1 more) |
| data-layer | other | **DIVERGENCE** | `core.model` -> `core.util` |
| language-processing | content-pipeline | **DIVERGENCE** | `core.llm_services` -> `core.elastic`; `core.semantic_search` -> `core.content_recommender` (+1 more) |
| language-processing | data-layer | **CONVERGENCE** | `core.crowd_translations` -> `core.model`; `core.language` -> `core.model` (+5 more) |
| language-processing | learning-system | **DIVERGENCE** | `core.llm_services` -> `core.bookmark_operations`; `core.llm_services` -> `core.word_scheduling` |
| language-processing | other | **CONVERGENCE** | `core.language` -> `core.util`; `core.semantic_search` -> `core.util` |
| learning-system | content-pipeline | **ABSENCE** | (none) |
| learning-system | data-layer | **CONVERGENCE** | `core.bookmark_operations` -> `core.model`; `core.bookmark_quality` -> `core.model` (+2 more) |
| learning-system | language-processing | **CONVERGENCE** | `core.bookmark_operations` -> `core.tokenization`; `core.word_scheduling` -> `core.llm_services` |
| learning-system | other | **ABSENCE** | (none) |
| learning-system | user-management | **ABSENCE** | (none) |
| operations | content-pipeline | **CONVERGENCE** | `operations.crawler` -> `core.content_retriever` |
| operations | data-layer | **CONVERGENCE** | `operations.crawler` -> `core.model`; `operations.report_generator` -> `core.model` |
| operations | language-processing | **ABSENCE** | (none) |
| operations | learning-system | **ABSENCE** | (none) |
| operations | other | **ABSENCE** | (none) |
| operations | user-management | **CONVERGENCE** | `operations.crawler` -> `core.emailer` |
| other | data-layer | **CONVERGENCE** | `core.util` -> `core.model`; `core.verbal_flashcards` -> `core.model` |
| other | language-processing | **DIVERGENCE** | `core.util` -> `core.language`; `core.util` -> `core.tokenization` |
| other | learning-system | **DIVERGENCE** | `core.verbal_flashcards` -> `core.word_scheduling` |
| user-management | data-layer | **CONVERGENCE** | `core.account_management` -> `core.model`; `core.badges` -> `core.model` (+5 more) |
| user-management | learning-system | **ABSENCE** | (none) |
| user-management | other | **CONVERGENCE** | `core.friends` -> `core.util` |