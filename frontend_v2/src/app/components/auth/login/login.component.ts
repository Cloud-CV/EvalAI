import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';
import { GlobalService } from '../../../services/global.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { Router } from '@angular/router';

/**
 * Component Class
 */
@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
})
export class LoginComponent implements OnInit {
  isNameFocused = false;
  isPasswordFocused = false;

  /**
   * Route path for challenge list
   */
  challengesRoute = '/challenges/all';

  /**
   * Route path for login
   */
  loginRoute = '/auth/login';

  /**
   * Route path for signup
   */
  signupRoute = '/auth/signup';

  /**
   * All challenges common route path
   */
  allChallengesRoutePathCommon = '/challenges/all';

  /**
   * Is user Logged in
   */
  isLoggedIn: any = false;

  /**
   * Constructor.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection
   * @param authService  AuthService Injection
   * @param router  Router Injection.
   * @param endpointsService EndPointsService Injection.
   */
  constructor(
    private globalService: GlobalService,
    private apiService: ApiService,
    public authService: AuthService,
    private router: Router,
    private endpointsService: EndpointsService
  ) {}

  /**
   * Constructor on initialization
   */
  ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
    this.authService.resetForm();
  }

  /**
   * Constructor.
   * @param self  Router Injection.
   */
  redirectCheck(self) {
    let redirectTo = this.challengesRoute;
    const REDIRECT_URL = self.globalService.getData(self.globalService.redirectStorageKey);
    if (REDIRECT_URL && REDIRECT_URL['path']) {
      redirectTo = REDIRECT_URL['path'];
      self.globalService.deleteData(self.globalService.redirectStorageKey);
    }
    self.router.navigate([redirectTo]);
  }

  // Function to login
  userLogin(loginFormValid) {
    if (!loginFormValid) {
      this.globalService.stopLoader();
      return;
    }

    this.globalService.startLoader('Taking you to EvalAI!');

    const LOGIN_BODY = {
      username: this.authService.getUser['name'],
      password: this.authService.getUser['password'],
    };

    this.apiService.postUrl(this.endpointsService.loginURL(), LOGIN_BODY).subscribe(
      (data) => {
        this.globalService.storeData(this.globalService.authStorageKey, data['token']);
        this.authService.loggedIn(true);
        this.authService.setRefreshJWT();
        this.globalService.stopLoader();
        this.redirectCheck(this);
      },

      (err) => {
        this.globalService.stopLoader();

        if (err.status === 400) {
          this.authService.isFormError = true;
          try {
            const non_field_errors = typeof err.error.non_field_errors !== 'undefined';
            if (non_field_errors) {
              this.authService.FormError = err.error.non_field_errors[0];
            }
          } catch (error) {
            setTimeout(() => {
              this.globalService.showToast('Error', 'Unable to Login.Please Try Again!', 5);
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
