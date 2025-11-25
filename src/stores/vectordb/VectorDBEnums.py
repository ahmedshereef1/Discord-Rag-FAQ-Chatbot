from enum import Enum

class VectorDBEnums(Enum):
    QDRANT = "QDRANT"
    PGVECTOR = "PGVECTOR"

class DistanceMethodEnums(Enum):
    COSINE = "cosine"
    DOT = "dot"

class PgVectorTableSchemeEnums(Enum):
    ID = "id"
    TEXT = "text"
    VECTOR = "vector"
    CHUNK_ID = "chunk_id"
    METADATA = "metadata"
    _PREFIX = "pgvector"

class PgVectorDistanceMethodEnums(Enum):
    VECTOR_L2_OPS = "vector_l2_ops"              # For L2/Euclidean distance
    VECTOR_COSINE_OPS = "vector_cosine_ops"      # For cosine distance
    VECTOR_IP_OPS = "vector_ip_ops"              # For inner product
    VECTOR_L1_OPS = "vector_l1_ops"              # For L1 distance (0.7.0+)

class PgVectorIndexTypeEnums(Enum):
    HNSW = "hnsw"           # Hierarchical Navigable Small World (default, fastest)
    IVFFLAT = "ivfflat"     # Inverted File with Flat compression (memory efficient)


