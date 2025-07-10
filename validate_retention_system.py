#!/usr/bin/env python3
"""
AWS Retention System Validation Script

This script validates that the AWS retention system is working correctly
and is ready for production deployment.
"""

import os
import sys
import django
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.dev')
django.setup()

from challenges.models import Challenge, ChallengePhase
from challenges.aws_utils import (
    calculate_retention_period_days,
    map_retention_days_to_aws_values,
    get_log_group_name,
    set_cloudwatch_log_retention,
    calculate_submission_retention_date,
    update_challenge_log_retention_on_approval,
    update_challenge_log_retention_on_restart,
    update_challenge_log_retention_on_task_def_registration,
)
from jobs.models import Submission
from django.core.management import call_command
from io import StringIO


class RetentionSystemValidator:
    """Validates the AWS retention system"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def log_result(self, test_name, success, message, warning=False):
        """Log test result"""
        if warning:
            print(f"⚠️  {test_name}: {message}")
            self.warnings += 1
        elif success:
            print(f"✅ {test_name}: {message}")
            self.passed += 1
        else:
            print(f"❌ {test_name}: {message}")
            self.failed += 1
    
    def test_core_functions(self):
        """Test core retention functions"""
        print("\n🔍 Testing Core Functions")
        print("-" * 30)
        
        try:
            # Test retention calculations
            now = timezone.now()
            future_date = now + timedelta(days=10)
            past_date = now - timedelta(days=5)
            
            future_retention = calculate_retention_period_days(future_date)
            past_retention = calculate_retention_period_days(past_date)
            
            if future_retention > 30:
                self.log_result("Future Retention Calculation", True, f"{future_retention} days")
            else:
                self.log_result("Future Retention Calculation", False, f"Expected >30, got {future_retention}")
            
            if past_retention > 0:
                self.log_result("Past Retention Calculation", True, f"{past_retention} days")
            else:
                self.log_result("Past Retention Calculation", False, f"Expected >0, got {past_retention}")
            
            # Test AWS mapping
            aws_mapped = map_retention_days_to_aws_values(25)
            valid_aws_values = [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]
            
            if aws_mapped in valid_aws_values:
                self.log_result("AWS Value Mapping", True, f"25 days -> {aws_mapped} days")
            else:
                self.log_result("AWS Value Mapping", False, f"Invalid AWS value: {aws_mapped}")
            
            # Test log group naming
            log_group = get_log_group_name(123)
            if "challenge-pk-123" in log_group and "workers" in log_group:
                self.log_result("Log Group Naming", True, f"{log_group}")
            else:
                self.log_result("Log Group Naming", False, f"Invalid format: {log_group}")
                
        except Exception as e:
            self.log_result("Core Functions", False, f"Exception: {e}")
    
    def test_cloudwatch_integration(self):
        """Test CloudWatch integration with mocked AWS"""
        print("\n☁️  Testing CloudWatch Integration")
        print("-" * 35)
        
        try:
            # Get a test challenge
            challenge = Challenge.objects.first()
            if not challenge:
                self.log_result("CloudWatch Integration", False, "No challenges found")
                return
            
            # Mock AWS credentials and client
            mock_credentials = {
                'aws_access_key_id': 'test_key',
                'aws_secret_access_key': 'test_secret',
                'aws_region': 'us-east-1'
            }
            
            mock_client = MagicMock()
            mock_client.put_retention_policy.return_value = {
                'ResponseMetadata': {'HTTPStatusCode': 200}
            }
            
            with patch('challenges.utils.get_aws_credentials_for_challenge') as mock_get_creds:
                with patch('challenges.aws_utils.get_boto3_client') as mock_get_client:
                    mock_get_creds.return_value = mock_credentials
                    mock_get_client.return_value = mock_client
                    
                    # Test setting retention
                    result = set_cloudwatch_log_retention(challenge.pk)
                    
                    if result.get('success'):
                        self.log_result("CloudWatch Log Retention", True, 
                            f"Set {result['retention_days']} days for challenge {challenge.pk}")
                    else:
                        self.log_result("CloudWatch Log Retention", False, 
                            f"Error: {result.get('error')}")
                    
                    # Verify AWS client was called
                    if mock_client.put_retention_policy.called:
                        self.log_result("AWS Client Called", True, "put_retention_policy was called")
                    else:
                        self.log_result("AWS Client Called", False, "put_retention_policy was not called")
                        
        except Exception as e:
            self.log_result("CloudWatch Integration", False, f"Exception: {e}")
    
    def test_management_commands(self):
        """Test management commands"""
        print("\n🎛️  Testing Management Commands")
        print("-" * 32)
        
        try:
            # Test status command
            out = StringIO()
            call_command('manage_retention', 'status', stdout=out)
            output = out.getvalue()
            
            if "Total submissions:" in output:
                self.log_result("Status Command", True, "Executed successfully")
            else:
                self.log_result("Status Command", False, "Missing expected output")
            
            # Test help command
            out = StringIO()
            call_command('manage_retention', stdout=out)
            output = out.getvalue()
            
            if "Available actions" in output or "help" in output.lower():
                self.log_result("Help Command", True, "Shows available actions")
            else:
                self.log_result("Help Command", False, "Help not working")
                
        except Exception as e:
            self.log_result("Management Commands", False, f"Exception: {e}")
    
    def test_submission_retention(self):
        """Test submission retention logic"""
        print("\n📁 Testing Submission Retention")
        print("-" * 31)
        
        try:
            # Find a challenge phase
            phase = ChallengePhase.objects.first()
            if not phase:
                self.log_result("Submission Retention", False, "No challenge phases found")
                return
            
            # Test private phase retention
            phase.is_public = False
            phase.save()
            
            retention_date = calculate_submission_retention_date(phase)
            if retention_date and phase.end_date:
                days_diff = (retention_date - phase.end_date).days
                if days_diff == 30:
                    self.log_result("Private Phase Retention", True, f"30 days after phase end")
                else:
                    self.log_result("Private Phase Retention", False, f"Expected 30 days, got {days_diff}")
            else:
                self.log_result("Private Phase Retention", False, "No retention date calculated")
            
            # Test public phase retention
            phase.is_public = True
            phase.save()
            
            retention_date = calculate_submission_retention_date(phase)
            if retention_date is None:
                self.log_result("Public Phase Retention", True, "Correctly returns None")
            else:
                self.log_result("Public Phase Retention", False, f"Should be None, got {retention_date}")
            
            # Reset phase
            phase.is_public = False
            phase.save()
            
        except Exception as e:
            self.log_result("Submission Retention", False, f"Exception: {e}")
    
    def test_integration_callbacks(self):
        """Test integration callbacks"""
        print("\n🔗 Testing Integration Callbacks")
        print("-" * 33)
        
        try:
            challenge = Challenge.objects.first()
            if not challenge:
                self.log_result("Integration Callbacks", False, "No challenges found")
                return
            
            # Mock the set_cloudwatch_log_retention function
            with patch('challenges.aws_utils.set_cloudwatch_log_retention') as mock_set_retention:
                with patch('challenges.aws_utils.settings') as mock_settings:
                    mock_settings.DEBUG = False
                    mock_set_retention.return_value = {"success": True, "retention_days": 30}
                    
                    # Test all callbacks
                    update_challenge_log_retention_on_approval(challenge)
                    update_challenge_log_retention_on_restart(challenge)
                    update_challenge_log_retention_on_task_def_registration(challenge)
                    
                    if mock_set_retention.call_count == 3:
                        self.log_result("Integration Callbacks", True, "All 3 callbacks executed")
                    else:
                        self.log_result("Integration Callbacks", False, 
                            f"Expected 3 calls, got {mock_set_retention.call_count}")
                        
        except Exception as e:
            self.log_result("Integration Callbacks", False, f"Exception: {e}")
    
    def test_error_handling(self):
        """Test error handling"""
        print("\n🛡️  Testing Error Handling")
        print("-" * 26)
        
        try:
            # Test with non-existent challenge
            result = set_cloudwatch_log_retention(999999)
            if "error" in result:
                self.log_result("Non-existent Challenge", True, "Error properly handled")
            else:
                self.log_result("Non-existent Challenge", False, "Error not handled")
            
            # Test with invalid retention days
            test_values = [0, -1, 10000]
            for value in test_values:
                mapped = map_retention_days_to_aws_values(value)
                if mapped > 0:
                    self.log_result(f"Invalid Value Handling ({value})", True, f"Mapped to {mapped}")
                else:
                    self.log_result(f"Invalid Value Handling ({value})", False, f"Invalid result: {mapped}")
                    
        except Exception as e:
            self.log_result("Error Handling", False, f"Exception: {e}")
    
    def test_database_models(self):
        """Test database model fields"""
        print("\n🗄️  Testing Database Models")
        print("-" * 28)
        
        try:
            # Test Challenge model
            challenge = Challenge.objects.first()
            if challenge and hasattr(challenge, 'log_retention_days_override'):
                self.log_result("Challenge Model Field", True, "log_retention_days_override exists")
            else:
                self.log_result("Challenge Model Field", False, "log_retention_days_override missing")
            
            # Test Submission model
            submission = Submission.objects.first()
            if submission:
                required_fields = ['retention_eligible_date', 'is_artifact_deleted']
                missing_fields = [f for f in required_fields if not hasattr(submission, f)]
                
                if not missing_fields:
                    self.log_result("Submission Model Fields", True, "All retention fields exist")
                else:
                    self.log_result("Submission Model Fields", False, f"Missing: {missing_fields}")
            else:
                self.log_result("Submission Model Fields", True, "No submissions to test (OK)")
                
        except Exception as e:
            self.log_result("Database Models", False, f"Exception: {e}")
    
    def run_validation(self):
        """Run complete validation"""
        print("🚀 AWS Retention System Validation")
        print("=" * 50)
        print("This script validates the AWS retention system for production readiness.")
        print()
        
        # Run all tests
        self.test_core_functions()
        self.test_cloudwatch_integration()
        self.test_management_commands()
        self.test_submission_retention()
        self.test_integration_callbacks()
        self.test_error_handling()
        self.test_database_models()
        
        # Generate report
        self.generate_report()
        
        return self.failed == 0
    
    def generate_report(self):
        """Generate validation report"""
        print("\n" + "=" * 50)
        print("📋 VALIDATION REPORT")
        print("=" * 50)
        
        total_tests = self.passed + self.failed + self.warnings
        
        print(f"\n📊 Test Results:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {self.passed} ✅")
        print(f"  Failed: {self.failed} ❌")
        print(f"  Warnings: {self.warnings} ⚠️")
        
        if total_tests > 0:
            pass_rate = (self.passed / total_tests) * 100
            print(f"  Pass Rate: {pass_rate:.1f}%")
        
        # Production readiness assessment
        print(f"\n🚀 Production Readiness:")
        if self.failed == 0:
            print("  ✅ READY FOR PRODUCTION")
            print("  All critical tests passed successfully.")
            
            print(f"\n✅ Deployment Checklist:")
            print("  ✅ Core functions working")
            print("  ✅ AWS integration tested (mocked)")
            print("  ✅ Management commands functional")
            print("  ✅ Error handling robust")
            print("  ✅ Database models updated")
            
            print(f"\n🔧 Production Setup Steps:")
            print("  1. Configure AWS credentials (IAM role or access keys)")
            print("  2. Ensure CloudWatch permissions:")
            print("     - logs:CreateLogGroup")
            print("     - logs:PutRetentionPolicy")
            print("     - logs:DeleteLogGroup")
            print("  3. Test with a small challenge first")
            print("  4. Monitor CloudWatch for errors")
            print("  5. Set up alerts for retention failures")
            print("  6. Schedule regular cleanup jobs")
            
        elif self.failed <= 2:
            print("  ⚠️  READY WITH CAUTION")
            print("  Minor issues detected. Review failed tests.")
        else:
            print("  ❌ NOT READY")
            print("  Critical issues detected. Fix failed tests first.")
        
        print(f"\n🎉 Validation Complete!")
        
        return self.failed == 0


def main():
    """Main validation function"""
    validator = RetentionSystemValidator()
    is_ready = validator.run_validation()
    
    # Exit with appropriate code
    sys.exit(0 if is_ready else 1)


if __name__ == "__main__":
    main() 