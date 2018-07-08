import { Component, OnInit, Inject } from '@angular/core';
import { ViewChildren, QueryList, AfterViewInit } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { InputComponent } from '../input/input.component';
import { WindowService } from '../services/window.service';
import { ApiService } from '../services/api.service';
import { GlobalService } from '../global.service';
import { Router, ActivatedRoute} from '@angular/router';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit, AfterViewInit {
  API_PATH = 'auth/login/';
  ALL_FORMS: any = {};
  loginForm = 'formlogin';
  @ViewChildren('formlogin')
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

    this.ALL_FORMS[this.loginForm] = this.components;
  }

  formValidate(formname) {
    this.globalService.formValidate(this.ALL_FORMS[this.loginForm], this.formSubmit, this);
  }

  formSubmit(self) {
    const LOGIN_BODY = JSON.stringify({
      username: self.globalService.formValueForLabel(self.ALL_FORMS[self.loginForm], 'username'),
      password: self.globalService.formValueForLabel(self.ALL_FORMS[self.loginForm], 'password')
    });
    self.apiService.postUrl(self.API_PATH, LOGIN_BODY).subscribe(
      data => {
        // Success Message in data.message
        // TODO: redirect to dashboard page
        self.globalService.storeData('authtoken', data);
      },
      err => {
        self.globalService.handleFormError(self.ALL_FORMS[self.loginForm], err);
      },
      () => console.log('LOGIN-FORM-SUBMITTED')
    );
  }
}
