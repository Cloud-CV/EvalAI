import { Injectable } from '@angular/core';
import { GlobalService } from './global.service';
import { EndpointsService } from './endpoints.service';
import { ApiService } from './api.service';
import { BehaviorSubject } from 'rxjs';
import { Router } from '@angular/router';

@Injectable()
export class AuthService {
  authState = { isLoggedIn: false };
  private authStateSource = new BehaviorSubject(this.authState);
  change = this.authStateSource.asObservable();

  isAuth = false;
  isMail = true;
  // getUser for signup
  regUser = {};
  // useDetails for login
  getUser = {};
  // color to show password strength
  color = {};
  isResetPassword = false;
  // form error
  isFormError = false;
  FormError = {};

  // default parameters
  isLoader = false;
  regMsg = '';
  wrnMsg = {};
  isValid = {};
  deliveredMsg = '';
  canShowPassword = false;
  canShowConfirmPassword = false;

  /**
   * Constructor.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   * @param endpointsService  EndpointsService Injection.
   */
  constructor(
    private globalService: GlobalService,
    private apiService: ApiService,
    private endpointsService: EndpointsService,
    private router: Router
  ) {}

  /**
   * Call this to update authentication state.
   * @param state  New Authentication state
   */
  authStateChange(state) {
    this.authState = state;
    this.authStateSource.next(this.authState);
    this.isAuth = this.authState.isLoggedIn;
  }

  /**
   * To affirm that user is logged in
   * @param autoFetchUserDetails  User details fetch flag
   */
  loggedIn(autoFetchUserDetails = false) {
    this.authStateChange({ isLoggedIn: true, username: '' });
    if (autoFetchUserDetails) {
      this.fetchUserDetails();
    }
  }

  /**
   * Log Out Trigger
   */
  logOut() {
    const temp = { isLoggedIn: false };
    const routePath = '';
    this.globalService.deleteData(this.globalService.authStorageKey);
    this.authStateChange(temp);
    this.router.navigate([routePath]);
    this.globalService.showToast('info', 'Successfully logged out!');
  }

  /**
   * User Details fetch Trigger
   */
  fetchUserDetails() {
    const API_PATH = 'auth/user/';
    const SELF = this;
    this.apiService.getUrl(API_PATH).subscribe(
      (data) => {
        const TEMP = Object.assign({ isLoggedIn: true }, SELF.authState, data);
        SELF.authStateChange(TEMP);
      },
      (err) => {
        this.globalService.showToast('info', 'Timeout, Please login again to continue!');
        this.globalService.resetStorage();
        this.authState = { isLoggedIn: false };
        SELF.globalService.handleApiError(err, false);
      },
      () => {}
    );
  }

  /**
   * Calculating Password Strength (Not being called as of now)
   * TODO: make use of it
   */
  passwordStrength(password) {
    // Regular Expressions.
    const REGEX = new Array();
    REGEX.push('[A-Z]', '[a-z]', '[0-9]', '[$$!%*#?&]');

    let passed = 0;
    // Validate for each Regular Expression.
    for (let i = 0; i < REGEX.length; i++) {
      if (new RegExp(REGEX[i]).test(password)) {
        passed++;
      }
    }
    // Validate for length of Password.
    if (passed > 2 && password.length > 8) {
      passed++;
    }

    let color = '';
    let strength = '';
    if (passed === 1) {
      strength = 'Weak';
      color = 'red';
    } else if (passed === 2) {
      strength = 'Average';
      color = 'darkorange';
    } else if (passed === 3) {
      strength = 'Good';
      color = 'green';
    } else if (passed === 4) {
      strength = 'Strong';
      color = 'darkgreen';
    } else if (passed === 5) {
      strength = 'Very Strong';
      color = 'darkgreen';
    }
    return [strength, color];
  }

  /**
   * Check if user is loggedIn and trigger logIn if token present but not loggedIn
   */
  isLoggedIn() {
    const token = this.globalService.getAuthToken();
    if (token) {
      if (!this.authState['isLoggedIn']) {
        this.loggedIn(true);
      }
      return true;
    } else {
      if (this.authState['isLoggedIn']) {
        this.logOut();
      }
    }
  }

  /**
   * User Details fetch Trigger
   * @param token
   * @param success
   * @param error
   */
  verifyEmail(token, success = () => {}, error = () => {}) {
    const API_PATH = this.endpointsService.verifyEmailURL();
    const SELF = this;
    const BODY = JSON.stringify({
      key: token,
    });
    this.apiService.postUrl(API_PATH, BODY).subscribe(
      (data) => {
        success();
      },
      (err) => {
        error();
        SELF.globalService.handleApiError(err);
      },
      () => {}
    );
  }

  /**
   * Fetch JWT for submission Auth Token
   */
  setRefreshJWT() {
    const API_PATH = 'accounts/user/get_auth_token';
    this.apiService.getUrl(API_PATH).subscribe(
      (data) => {
        this.globalService.storeData('refreshJWT', data['token']);
      },
      (err) => {
        this.globalService.showToast('info', 'Could not fetch Auth Token');
        return false;
      },
      () => {}
    );
  }

  // toggle password visibility
  togglePasswordVisibility() {
    this.canShowPassword = !this.canShowPassword;
  }

  // toggle confirm password visibility
  toggleConfirmPasswordVisibility() {
    this.canShowConfirmPassword = !this.canShowConfirmPassword;
  }

  resetForm() {
    // getUser for signup
    this.regUser = {};
    // useDetails for login
    this.getUser = {};

    // reset error msg
    this.wrnMsg = {};

    // switch off form errors
    this.isFormError = false;

    // reset form when link sent for reset password
    this.isMail = true;

    // reset the eye icon and type to password
    this.canShowPassword = false;
    this.canShowConfirmPassword = false;
  }
}
