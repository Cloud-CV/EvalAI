import { Component, OnInit, Inject } from '@angular/core';
import { ViewChildren, QueryList, AfterViewInit } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { InputComponent } from '../../../components/utility/input/input.component';
import { WindowService } from '../../../services/window.service';
import { ApiService } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';
import { GlobalService } from '../../../services/global.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { Router, ActivatedRoute} from '@angular/router';

/**
 * Component Class
 */
@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit, AfterViewInit {

  isnameFocused = false;
  ispasswordFocused = false;

  /**
   * Route path for dashboard
   */
  dashboardRoute = '/dashboard';

  /**
   * Route path for login
   */
  loginRoute = '/auth/login';

  /**
   * Route path for signup
   */
  signupRoute = '/auth/signup';

  /**
   * Constructor.
   * @param document  window document injection
   * @param windowService
   * @param apiService  ApiService Injection
   * @param authService  AuthService Injection
   * @param router  Router Injection.
   * @param route  ActivatedRoute Injection.
   * @param globalService  GlobalService Injection.
   * @param endpointsService
   */
  constructor(@Inject(DOCUMENT) private document: Document,
              private windowService: WindowService,
              private globalService: GlobalService,
              private apiService: ApiService,
              public authService: AuthService,
              private route: ActivatedRoute,
              private router: Router,
              private endpointsService: EndpointsService) {
  }

  /**
   * Constructor on initialization
   */
  ngOnInit() {
    this.authService.resetForm();
  }

  /**
   * After view is initialized.
   */
  ngAfterViewInit() {
  }

  /**
   * Constructor.
   * @param self  Router Injection.
   */
  redirectCheck(self) {
    let redirectTo = this.dashboardRoute;
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
      'username': this.authService.getUser['name'],
      'password': this.authService.getUser['password'],
    };

    this.apiService.postUrl(this.endpointsService.loginURL(), LOGIN_BODY).subscribe(
      data => {
        this.globalService.storeData(this.globalService.authStorageKey, data['token']);
        this.authService.loggedIn(true);
        this.globalService.stopLoader();
        this.redirectCheck(this);
      },

      err => {
        this.globalService.stopLoader();

        if (err.status === 400) {
          this.authService.isFormError = true;
          try {
            const non_field_errors = typeof (err.error.non_field_errors) !== 'undefined';
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
