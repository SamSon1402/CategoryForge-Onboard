from category_forge.core.deployment import DeploymentController
from category_forge.core.schemas import DeploymentRecord, DeploymentState


def test_release_state_machine():
    ctl = DeploymentController()
    record = DeploymentRecord(customer_id="c", site_id="line-1", bundle_version=2, bundle_sha256="abc")
    record = ctl.validate(record)
    record = ctl.shadow(record)
    record = ctl.canary(record, 10)
    record = ctl.promote(record)
    assert record.state == DeploymentState.ACTIVE
    assert record.canary_percent == 100
