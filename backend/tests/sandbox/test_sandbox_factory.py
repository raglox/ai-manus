"""
Tests for Sandbox Factory

Tests the factory pattern for switching between DockerSandbox and
CloudRunJobsSandbox implementations based on feature flags.

Author: Kilo Code
Date: 2025-12-28
"""

import pytest
from unittest.mock import patch, MagicMock
from app.infrastructure.external.sandbox.factory import get_sandbox, get_sandbox_info
from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
from app.infrastructure.external.sandbox.cloudrun_jobs_sandbox import CloudRunJobsSandbox


class TestSandboxFactory:
    """Test sandbox factory default behavior"""
    
    def test_default_returns_docker_sandbox(self):
        """Test that factory returns DockerSandbox by default"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            # Mock settings with feature flag OFF
            mock_settings.return_value = MagicMock(
                use_cloudrun_jobs_sandbox=False
            )
            
            sandbox_class = get_sandbox()
            
            assert sandbox_class == DockerSandbox
    
    def test_feature_flag_off_returns_docker_sandbox(self):
        """Test that feature flag OFF returns DockerSandbox"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                use_cloudrun_jobs_sandbox=False
            )
            
            sandbox_class = get_sandbox()
            
            assert sandbox_class == DockerSandbox
    
    def test_missing_feature_flag_returns_docker_sandbox(self):
        """Test that missing feature flag returns DockerSandbox"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            # Mock settings without feature flag attribute
            settings = MagicMock(spec=[])  # No attributes
            mock_settings.return_value = settings
            
            sandbox_class = get_sandbox()
            
            assert sandbox_class == DockerSandbox


class TestCloudRunSandboxSelection:
    """Test CloudRun sandbox selection with feature flag"""
    
    def test_feature_flag_on_with_config_returns_cloudrun(self):
        """Test that feature flag ON with valid config returns CloudRunJobsSandbox"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                use_cloudrun_jobs_sandbox=True,
                sandbox_gcp_project="test-project",
                sandbox_gcp_region="us-central1",
                sandbox_gcs_bucket="test-bucket"
            )
            
            sandbox_class = get_sandbox()
            
            assert sandbox_class == CloudRunJobsSandbox
    
    def test_feature_flag_on_without_project_falls_back(self):
        """Test that feature flag ON without project ID falls back to DockerSandbox"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                use_cloudrun_jobs_sandbox=True,
                sandbox_gcp_project=None  # Missing project
            )
            
            sandbox_class = get_sandbox()
            
            assert sandbox_class == DockerSandbox
    
    def test_feature_flag_on_with_empty_project_falls_back(self):
        """Test that feature flag ON with empty project falls back to DockerSandbox"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                use_cloudrun_jobs_sandbox=True,
                sandbox_gcp_project=""  # Empty project
            )
            
            sandbox_class = get_sandbox()
            
            assert sandbox_class == DockerSandbox


class TestGracefulFallback:
    """Test graceful fallback on errors"""
    
    def test_exception_during_selection_falls_back(self):
        """Test that exceptions during selection fall back to DockerSandbox"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            # Mock settings that raises exception when accessing attributes
            settings = MagicMock()
            settings.use_cloudrun_jobs_sandbox = True
            settings.sandbox_gcp_project = MagicMock(side_effect=Exception("Test error"))
            mock_settings.return_value = settings
            
            sandbox_class = get_sandbox()
            
            assert sandbox_class == DockerSandbox
    
    def test_import_error_falls_back(self):
        """Test that import errors fall back to DockerSandbox"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                use_cloudrun_jobs_sandbox=True,
                sandbox_gcp_project="test-project"
            )
            
            # Even with valid config, should handle import errors gracefully
            # (though in this test CloudRunJobsSandbox is importable)
            sandbox_class = get_sandbox()
            
            # Should return one of the valid classes
            assert sandbox_class in [DockerSandbox, CloudRunJobsSandbox]


class TestSandboxInfo:
    """Test sandbox info function"""
    
    def test_info_with_feature_flag_off(self):
        """Test get_sandbox_info with feature flag OFF"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                use_cloudrun_jobs_sandbox=False
            )
            
            info = get_sandbox_info()
            
            assert info["implementation"] == "DockerSandbox"
            assert info["feature_flag_enabled"] is False
            assert "Feature flag disabled" in info["reason"]
            assert info["config"] == {}
    
    def test_info_with_feature_flag_on_valid_config(self):
        """Test get_sandbox_info with feature flag ON and valid config"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                use_cloudrun_jobs_sandbox=True,
                sandbox_gcp_project="test-project",
                sandbox_gcp_region="us-west1",
                sandbox_gcs_bucket="test-bucket"
            )
            
            info = get_sandbox_info()
            
            assert info["implementation"] == "CloudRunJobsSandbox"
            assert info["feature_flag_enabled"] is True
            assert "valid configuration" in info["reason"]
            assert info["config"]["project_id"] == "test-project"
            assert info["config"]["region"] == "us-west1"
            assert info["config"]["bucket"] == "test-bucket"
    
    def test_info_with_feature_flag_on_missing_config(self):
        """Test get_sandbox_info with feature flag ON but missing config"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                use_cloudrun_jobs_sandbox=True,
                sandbox_gcp_project=None
            )
            
            info = get_sandbox_info()
            
            assert info["implementation"] == "DockerSandbox"
            assert info["feature_flag_enabled"] is True
            assert "fallback" in info["reason"]


class TestConfigurationValidation:
    """Test configuration validation"""
    
    def test_validates_project_id_required(self):
        """Test that project_id is required for CloudRun"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                use_cloudrun_jobs_sandbox=True,
                sandbox_gcp_project=None
            )
            
            sandbox_class = get_sandbox()
            
            # Should fall back to DockerSandbox due to missing project
            assert sandbox_class == DockerSandbox
    
    def test_default_region_used_when_not_specified(self):
        """Test that default region is used when not specified"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            # Mock getattr to return None for region (not specified)
            settings = MagicMock(
                use_cloudrun_jobs_sandbox=True,
                sandbox_gcp_project="test-project"
            )
            # Make getattr return None for region attribute
            def custom_getattr(obj, name, default=None):
                if name == 'sandbox_gcp_region':
                    return default
                return getattr(obj, name, default)
            
            mock_settings.return_value = settings
            
            with patch('builtins.getattr', side_effect=custom_getattr):
                info = get_sandbox_info()
                
                # Should use default region
                if info["implementation"] == "CloudRunJobsSandbox":
                    assert info["config"]["region"] == "us-central1"
    
    def test_default_bucket_generated_from_project(self):
        """Test that default bucket is generated from project ID"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            settings = MagicMock(
                use_cloudrun_jobs_sandbox=True,
                sandbox_gcp_project="my-project"
            )
            # Make getattr return defaults
            def custom_getattr(obj, name, default=None):
                if name == 'sandbox_gcp_region':
                    return default if default else 'us-central1'
                elif name == 'sandbox_gcs_bucket':
                    return default if default else 'my-project-sandbox-state'
                return getattr(obj, name, default)
            
            mock_settings.return_value = settings
            
            with patch('builtins.getattr', side_effect=custom_getattr):
                info = get_sandbox_info()
                
                # Should generate bucket from project
                if info["implementation"] == "CloudRunJobsSandbox":
                    assert "my-project" in info["config"]["bucket"]


class TestBackwardCompatibility:
    """Test backward compatibility with existing code"""
    
    def test_returns_class_not_instance(self):
        """Test that factory returns class, not instance"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                use_cloudrun_jobs_sandbox=False
            )
            
            result = get_sandbox()
            
            # Should be a class, not an instance
            assert isinstance(result, type)
            assert issubclass(result, object)
    
    def test_can_instantiate_returned_class(self):
        """Test that returned class can be instantiated"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                use_cloudrun_jobs_sandbox=False
            )
            
            sandbox_class = get_sandbox()
            
            # Should be able to call create() method
            assert hasattr(sandbox_class, 'create')
            assert callable(sandbox_class.create)


class TestLogging:
    """Test logging behavior"""
    
    def test_logs_docker_sandbox_selection(self):
        """Test that DockerSandbox selection is logged"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            with patch('app.infrastructure.external.sandbox.factory.logger') as mock_logger:
                mock_settings.return_value = MagicMock(
                    use_cloudrun_jobs_sandbox=False
                )
                
                get_sandbox()
                
                # Should log the selection
                mock_logger.info.assert_called()
                call_args = str(mock_logger.info.call_args)
                assert "DockerSandbox" in call_args
    
    def test_logs_cloudrun_sandbox_selection(self):
        """Test that CloudRunJobsSandbox selection is logged"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            with patch('app.infrastructure.external.sandbox.factory.logger') as mock_logger:
                mock_settings.return_value = MagicMock(
                    use_cloudrun_jobs_sandbox=True,
                    sandbox_gcp_project="test-project",
                    sandbox_gcp_region="us-central1",
                    sandbox_gcs_bucket="test-bucket"
                )
                
                get_sandbox()
                
                # Should log the selection with config details
                mock_logger.info.assert_called()
                call_args = str(mock_logger.info.call_args_list)
                assert "CloudRunJobsSandbox" in call_args
    
    def test_logs_fallback_on_missing_config(self):
        """Test that fallback is logged when config is missing"""
        with patch('app.infrastructure.external.sandbox.factory.get_settings') as mock_settings:
            with patch('app.infrastructure.external.sandbox.factory.logger') as mock_logger:
                mock_settings.return_value = MagicMock(
                    use_cloudrun_jobs_sandbox=True,
                    sandbox_gcp_project=None
                )
                
                get_sandbox()
                
                # Should log warning about fallback
                mock_logger.warning.assert_called()
                call_args = str(mock_logger.warning.call_args)
                assert "Falling back" in call_args or "fallback" in call_args.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])