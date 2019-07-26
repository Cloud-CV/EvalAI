import {Component, OnInit} from '@angular/core';
import {AuthService} from '../../../services/auth.service';
import {ApiService} from '../../../services/api.service';
import {EndpointsService} from '../../../services/endpoints.service';
import {GlobalService} from '../../../services/global.service';

@Component({
  selector: 'app-reset-password',
  templateUrl: './reset-password.component.html',
  styleUrls: ['./reset-password.component.scss']
})
export class ResetPasswordComponent implements OnInit {

  isemailFocused = false;

  /**
   * Login route path
   */
  loginRoute = '/auth/login';

  /**
   * Signup route path
   */
  signupRoute = '/auth/signup';

  /**
   * Reset-password route path
   */
  resetPasswordRoute = '/auth/reset-password';

  /**
   *
   * @param authService
   * @param globalService
   * @param apiService
   * @param endpointService
   */
  constructor(public authService: AuthService, private globalService: GlobalService, private apiService: ApiService,
              private endpointService: EndpointsService) {
  }

  ngOnInit() {
    this.authService.resetForm();
  }

  // function to reset password
  resetPassword(resetPassFormValid) {
    if (resetPassFormValid) {
      this.globalService.startLoader('Sending Mail');

      const RESET_BODY = JSON.stringify({
        email: this.authService.getUser['email']
      });

      const API_PATH = this.endpointService.resetPasswordURL();

      this.apiService.postUrl(API_PATH, RESET_BODY).subscribe(
        response => {
          this.authService.isMail = false;
          this.authService.getUser['error'] = false;
          this.authService.isFormError = false;
          this.authService.deliveredMsg = response.detail;
          this.authService.getUser['email'] = '';
          this.globalService.stopLoader();
        },

        err => {
          this.authService.isFormError = true;
          this.authService.FormError = 'Something went wrong. Please try again';
          this.globalService.stopLoader();
        },

        () => {}
      );
    } else {
      this.globalService.stopLoader();
    }
  }
}
