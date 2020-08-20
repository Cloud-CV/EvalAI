import { Component, OnInit, Inject } from '@angular/core';
import { AfterViewInit } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { WindowService } from '../../../services/window.service';
import { ApiService } from '../../../services/api.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { GlobalService } from '../../../services/global.service';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../../services/auth.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-signup',
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.scss'],
})
export class SignupComponent implements OnInit, AfterViewInit {
  color = '';
  message = '';

  isnameFocused = false;
  ispasswordFocused = false;
  iscnfrmpasswordFocused = false;
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
   * Constructor.
   * @param document  window document Injection.
   * @param windowService  ActivatedRoute Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   * @param authService
   * @param router  Router Injection.
   * @param route  ActivatedRoute Injection.
   * @param endpointsService
   */
  constructor(
    @Inject(DOCUMENT) private document: Document,
    private windowService: WindowService,
    private globalService: GlobalService,
    private apiService: ApiService,
    public authService: AuthService,
    private route: ActivatedRoute,
    private endpointsService: EndpointsService,
    private router: Router
  ) {}

  /**
   * Component init function.
   */
  ngOnInit() {}

  /**
   * Component after view initialized.
   */
  ngAfterViewInit() {}

  // Function to signup
  userSignUp(signupFormValid) {
    if (signupFormValid) {
      this.globalService.startLoader('Setting up your details!');
      const SIGNUP_BODY = JSON.stringify({
        username: this.authService.regUser['name'],
        email: this.authService.regUser['email'],
        password1: this.authService.regUser['password'],
        password2: this.authService.regUser['confirm_password'],
      });

      this.apiService.postUrl(this.endpointsService.signupURL(), SIGNUP_BODY).subscribe(
        (data) => {
          if (data.status === 201) {
            this.authService.isFormError = false;
            this.authService.regMsg = 'Registered successfully, Login to continue!';
          }

          // Success Message in data.message
          setTimeout(() => {
            this.globalService.showToast('success', 'Registered successfully. Please verify your email address!', 5);
          }, 1000);

          this.router.navigate([this.loginRoute]);
          this.globalService.stopLoader();
        },

        (err) => {
          this.globalService.stopLoader();
          if (err.status === 400) {
            this.authService.isFormError = true;
            let non_field_errors, isUsername_valid, isEmail_valid, isPassword1_valid, isPassword2_valid;
            try {
              non_field_errors = typeof err.error.non_field_errors !== 'undefined';
              isUsername_valid = typeof err.error.username !== 'undefined';
              isEmail_valid = typeof err.error.email !== 'undefined';
              isPassword1_valid = typeof err.error.password1 !== 'undefined';
              isPassword2_valid = typeof err.error.password2 !== 'undefined';
              if (non_field_errors) {
                this.authService.FormError = err.error.non_field_errors[0];
              } else if (isUsername_valid) {
                this.authService.FormError = err.error.username[0];
              } else if (isEmail_valid) {
                this.authService.FormError = err.error.email[0];
              } else if (isPassword1_valid) {
                this.authService.FormError = err.error.password1[0];
              } else if (isPassword2_valid) {
                this.authService.FormError = err.error.password2[0];
              }
            } catch (error) {
              setTimeout(() => {
                this.globalService.showToast('Error', 'Registration UnSuccessful.Please Try Again!', 5);
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

  // function to check password strength
  checkStrength(password) {
    const passwordStrength = this.authService.passwordStrength(password);
    this.message = passwordStrength[0];
    this.color = passwordStrength[1];
  }
}
