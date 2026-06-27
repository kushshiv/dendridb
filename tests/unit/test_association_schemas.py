import pytest
from pydantic import ValidationError

from dendridb.api.schemas.association import AssociationCreate


def test_association_create_validates_weight_bounds():
    with pytest.raises(ValidationError):
        AssociationCreate(
            namespace="team-a",
            source_type="memory_record",
            source_id="00000000-0000-0000-0000-000000000001",
            target_type="memory_record",
            target_id="00000000-0000-0000-0000-000000000002",
            weight=1.5,
        )
