"""
Sandbox Factory with Feature Flag Support

Provides safe switching between DockerSandbox and CloudRunJobsSandbox
implementations using environment-based feature flags.

Safety Features:
- Defaults to DockerSandbox (safe fallback)
- Graceful error handling with fallback to DockerSandbox
- Comprehensive logging for debugging
- Configuration validation

Author: Kilo Code
Date: 2025-12-28
"""

import logging
from typing import Type

from app.core.config import get_settings
from app.domain.external.sandbox import Sandbox
from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
from app.infrastructure.external.sandbox.cloudrun_jobs_sandbox import CloudRunJobsSandbox

logger = logging.getLogger(__name__)


def get_sandbox() -> Type[Sandbox]:
    """
    Get sandbox class based on configuration.
    
    Uses feature flag USE_CLOUDRUN_JOBS_SANDBOX to control selection.
    Defaults to DockerSandbox for safety and backward compatibility.
    
    Returns:
        Sandbox class (not instance) to be instantiated by the caller
        
    Safety:
        - Always defaults to DockerSandbox if feature flag is False
        - Falls back to DockerSandbox on any error
        - Logs all decisions for debugging
        
    Example:
        >>> sandbox_class = get_sandbox()
        >>> sandbox = await sandbox_class.create()
    """
    settings = get_settings()
    
    # Check feature flag
    use_cloudrun = getattr(settings, 'use_cloudrun_jobs_sandbox', False)
    
    if not use_cloudrun:
        logger.info("Sandbox selection: DockerSandbox (default - feature flag OFF)")
        return DockerSandbox
    
    # Feature flag is ON - validate CloudRun configuration
    try:
        logger.info("Feature flag ON - attempting to use CloudRunJobsSandbox")
        
        # Validate required configuration
        project_id = getattr(settings, 'sandbox_gcp_project', None)
        if not project_id:
            logger.warning(
                "CloudRunJobsSandbox enabled but SANDBOX_GCP_PROJECT not configured. "
                "Falling back to DockerSandbox"
            )
            return DockerSandbox
        
        region = getattr(settings, 'sandbox_gcp_region', 'us-central1')
        bucket = getattr(settings, 'sandbox_gcs_bucket', f"{project_id}-sandbox-state")
        
        logger.info(
            f"Sandbox selection: CloudRunJobsSandbox "
            f"(project={project_id}, region={region}, bucket={bucket})"
        )
        
        return CloudRunJobsSandbox
        
    except Exception as e:
        logger.error(
            f"Error selecting CloudRunJobsSandbox: {e}. "
            f"Falling back to DockerSandbox for safety",
            exc_info=True
        )
        return DockerSandbox


def get_sandbox_info() -> dict:
    """
    Get information about the currently selected sandbox implementation.
    
    Returns:
        Dict with sandbox selection details:
        - implementation: "DockerSandbox" or "CloudRunJobsSandbox"
        - feature_flag_enabled: Boolean
        - reason: String explaining the selection
        - config: Dict of relevant configuration values
        
    Example:
        >>> info = get_sandbox_info()
        >>> print(f"Using: {info['implementation']}")
    """
    settings = get_settings()
    use_cloudrun = getattr(settings, 'use_cloudrun_jobs_sandbox', False)
    
    info = {
        "feature_flag_enabled": use_cloudrun,
        "config": {}
    }
    
    if not use_cloudrun:
        info["implementation"] = "DockerSandbox"
        info["reason"] = "Feature flag disabled (USE_CLOUDRUN_JOBS_SANDBOX=false)"
        return info
    
    # Check configuration validity
    project_id = getattr(settings, 'sandbox_gcp_project', None)
    if not project_id:
        info["implementation"] = "DockerSandbox"
        info["reason"] = "CloudRun enabled but GCP project not configured (fallback)"
        return info
    
    # CloudRun is configured and enabled
    info["implementation"] = "CloudRunJobsSandbox"
    info["reason"] = "Feature flag enabled with valid configuration"
    info["config"] = {
        "project_id": project_id,
        "region": getattr(settings, 'sandbox_gcp_region', 'us-central1'),
        "bucket": getattr(settings, 'sandbox_gcs_bucket', f"{project_id}-sandbox-state")
    }
    
    return info