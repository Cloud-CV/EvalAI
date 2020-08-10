import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../../services/auth.service';
import { ApiService } from '../../../services/api.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { GlobalService } from '../../../services/global.service';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-reset-password-confirm',
  templateUrl: './reset-password-confirm.component.html',
  styleUrls: ['./reset-password-confirm.component.scss'],
})
export class ResetPasswordConfirmComponent implements OnInit {
  uid: any = '';
  token: any = '';

  isNewPassword1Focused = false;
  isNewPassword2Focused = false;

  /**
   * Login route path
   */
  loginRoute = '/auth/login';

  /**
   * Signup route path
   */
  signupRoute = '/auth/signup';

  constructor(
    public authService: AuthService,
    private apiService: ApiService,
    private endpointService: EndpointsService,
    private globalService: GlobalService,
    private route: ActivatedRoute
  ) {}

  ngOnInit() {
    this.route.params.subscribe((params) => {
      if (params['user_id']) {
        this.uid = params['user_id'];
      }
      if (params['reset_token']) {
        this.uid = params['reset_token'];
      }
    });
  }

  resetPasswordConfirm(resetconfirmFormValid) {
    if (resetconfirmFormValid) {
      this.globalService.startLoader('Resetting Your Password');

      const RESET_BODY = JSON.stringify({
        new_password1: this.authService.getUser['new_password1'],
        new_password2: this.authService.getUser['new_password2'],
        uid: this.uid,
        token: this.token,
      });

      const API_PATH = this.endpointService.resetPasswordConfirmURL();

      this.apiService.postUrl(API_PATH, RESET_BODY).subscribe(
        (response) => {
          this.authService.isResetPassword = true;
          this.authService.deliveredMsg = response.data.detail;
          this.globalService.stopLoader();
        },

        (err) => {
          this.globalService.stopLoader();
          if (err.status === 400) {
            this.authService.isFormError = true;
            let non_field_errors, token_valid, password1_valid, password2_valid;
            try {
              non_field_errors = typeof err.error.non_field_errors !== 'undefined';
              token_valid = typeof err.error.token !== 'undefined';
              password1_valid = typeof err.error.new_password1 !== 'undefined';
              password2_valid = typeof err.error.new_password2 !== 'undefined';
              if (non_field_errors) {
                this.authService.FormError = err.error.non_field_errors[0];
              } else if (token_valid) {
                this.authService.FormError = err.error.token[0];
              } else if (password1_valid) {
                this.authService.FormError = err.error.new_password1[0];
              } else if (password2_valid) {
                this.authService.FormError = err.error.new_password2[0];
              }
            } catch (error) {
              setTimeout(() => {
                this.authService.FormError = 'Something went wrong! Please refresh the page and try again.';
                this.globalService.showToast('Error', 'Reset Password UnSuccessful.Please Try Again!', 5);
              }, 1000);
            }
          } else {
            this.globalService.handleApiError(err);
          }
        },

        () => {}
      );
    }
  }
}
