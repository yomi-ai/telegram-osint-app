from nest.core import Module

from .healthchecks_service import HealthchecksService


@Module(
    providers=[HealthchecksService],
    exports=[HealthchecksService],
)
class HealthchecksModule: ...
