import { Component, OnInit, Inject } from '@angular/core';
import { ViewChildren, QueryList, AfterViewInit } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { InputComponent } from '../input/input.component';
import { WindowService } from '../services/window.service';
import { ApiService } from '../services/api.service';
import { GlobalService } from '../global.service';
import { Router, ActivatedRoute} from '@angular/router';

@Component({
  selector: 'app-signup',
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.scss']
})
export class SignupComponent implements OnInit, AfterViewInit {
  API_PATH = 'auth/registration/';
  ALL_FORMS: any = {};
  signupForm = 'formsignup';
  @ViewChildren('formsignup')
  components: QueryList<InputComponent>;
  constructor(@Inject(DOCUMENT) private document: Document,
              private windowService: WindowService,
              private globalService: GlobalService,
              private apiService: ApiService,
              private route: ActivatedRoute,
              private router: Router) { }

  ngOnInit() {
  }

  ngAfterViewInit() {
    // print array of CustomComponent objects
    // this.componentlist = this.components.toArray();

    this.ALL_FORMS[this.signupForm] = this.components;
  }

  formValidate(formname) {
    this.globalService.formValidate(this.ALL_FORMS[this.signupForm], this.formSubmit, this);
  }

  formSubmit(self) {
    const SIGNUP_BODY = JSON.stringify({
      username: self.globalService.formValueForLabel(self.ALL_FORMS[self.signupForm], 'username'),
      email: self.globalService.formValueForLabel(self.ALL_FORMS[self.signupForm], 'email'),
      password1: self.globalService.formValueForLabel(self.ALL_FORMS[self.signupForm], 'password'),
      password2: self.globalService.formValueForLabel(self.ALL_FORMS[self.signupForm], 'confirm password')
    });
    self.apiService.postUrl(self.API_PATH, SIGNUP_BODY).subscribe(
      data => {
        // Success Message in data.message
        setTimeout(() => {
          self.globalService.showToast('success', 'Registered successfully. Please verify your email address!', 5);
        }, 1000);
        self.router.navigate(['auth/login']);
      },
      err => {
        self.globalService.handleFormError(self.ALL_FORMS[self.signupForm], err);
      },
      () => console.log('SIGNUP-FORM-SUBMITTED')
    );
  }
}
