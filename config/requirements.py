from src.prompts import Framework


ISO27001_REQUIREMENTS = [
    "Information security policies must be formally documented and approved",
    "Access to systems and data must follow the principle of least privilege",
    "User access rights must be reviewed periodically",
    "Security incidents must be detected, logged, and reported",
    "Personal data must be protected against unauthorized access and disclosure",
]


GDPR_REQUIREMENTS = [
    "Personal data processing must be lawful, fair, and transparent",
    "Data must be collected for explicit and legitimate purposes",
    "Personal data must be protected by appropriate technical measures",
    "Data breaches must be detected and reported without undue delay",
]


def get_requirements(framework: Framework) -> list[str]:
    if framework == Framework.ISO27001:
        return ISO27001_REQUIREMENTS
    if framework == Framework.GDPR:
        return GDPR_REQUIREMENTS
    return []
