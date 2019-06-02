import { Component, OnInit, Inject } from '@angular/core';
import { ViewChildren, QueryList, AfterViewInit } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { InputComponent } from '../../../components/utility/input/input.component';
import { WindowService } from '../../../services/window.service';
import { ApiService } from '../../../services/api.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { GlobalService } from '../../../services/global.service';
import { Router, ActivatedRoute} from '@angular/router';

/**
 * Component Class
 */
@Component({
  selector: 'app-signup',
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.scss']
})
export class SignupComponent implements OnInit, AfterViewInit {

  /**
   * All forms in signup component
   */
  ALL_FORMS: any = {};

  /**
   * Form elements name in signup form
   */
  signupForm = 'formsignup';

  /**
   * Signup form elements
   */
  @ViewChildren('formsignup')
  components: QueryList<InputComponent>;

  /**
   * Constructor.
   * @param document  window document Injection.
   * @param windowService  ActivatedRoute Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   * @param router  Router Injection.
   * @param route  ActivatedRoute Injection.
   */
  constructor(@Inject(DOCUMENT) private document: Document,
              private windowService: WindowService,
              private globalService: GlobalService,
              private apiService: ApiService,
              private route: ActivatedRoute,
              private endpointsService: EndpointsService,
              private router: Router) { }

  /**
   * Component init function.
   */
  ngOnInit() {
  }

  /**
   * Component after view initialized.
   */
  ngAfterViewInit() {
    // print array of CustomComponent objects
    // this.componentlist = this.components.toArray();

    this.ALL_FORMS[this.signupForm] = this.components;
  }

  /**
   * Validate form function.
   * @param formname  Name of the form fields (#)
   */
  formValidate(formname) {
    this.globalService.formValidate(this.ALL_FORMS[this.signupForm], this.formSubmit, this);
  }

  /**
   * Form Submit function (Called after validation).
   * @param self  context value of this.
   */
  formSubmit(self) {
    const SIGNUP_BODY = JSON.stringify({
      username: self.globalService.formValueForLabel(self.ALL_FORMS[self.signupForm], 'username'),
      email: self.globalService.formValueForLabel(self.ALL_FORMS[self.signupForm], 'email'),
      password1: self.globalService.formValueForLabel(self.ALL_FORMS[self.signupForm], 'password'),
      password2: self.globalService.formValueForLabel(self.ALL_FORMS[self.signupForm], 'confirm password')
    });
    self.apiService.postUrl(self.endpointsService.signupURL(), SIGNUP_BODY).subscribe(
      data => {
        // Success Message in data.message
        setTimeout(() => {
          self.globalService.showToast('success', 'Registered successfully. Please verify your email address!', 5);
        }, 1000);
        self.router.navigate(['/auth/login']);
      },
      err => {
        self.globalService.handleFormError(self.ALL_FORMS[self.signupForm], err);
      },
      () => console.log('SIGNUP-FORM-SUBMITTED')
    );
  }
}
