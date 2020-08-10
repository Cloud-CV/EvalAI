import { Component, OnInit, Inject } from '@angular/core';
import { ViewChildren, QueryList, AfterViewInit } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { NGXLogger } from 'ngx-logger';

import { InputComponent } from '../../components/utility/input/input.component';
import { WindowService } from '../../services/window.service';
import { ApiService } from '../../services/api.service';
import { EndpointsService } from '../../services/endpoints.service';
import { GlobalService } from '../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-contact',
  templateUrl: './contact.component.html',
  styleUrls: ['./contact.component.scss'],
})
export class ContactComponent implements OnInit, AfterViewInit {
  /**
   * All forms in contact component
   */
  ALL_FORMS: any = {};

  /**
   * Form fields name
   */
  contactForm = 'formgroup';

  /**
   * Signup form components
   */
  @ViewChildren('formgroup')
  components: QueryList<InputComponent>;

  /**
   * List of components
   */
  componentlist: any;

  /**
   * Constructor.
   * @param document  Window document Injection.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   * @param endpointsService  EndpointsService Injection.
   */
  constructor(
    @Inject(DOCUMENT) private document: Document,
    private windowService: WindowService,
    private globalService: GlobalService,
    private apiService: ApiService,
    private route: ActivatedRoute,
    private router: Router,
    private endpointsService: EndpointsService,
    private logger: NGXLogger
  ) {}

  /**
   * Component on initialized.
   */
  ngOnInit() {
    this.globalService.scrollToTop();
  }

  /**
   * Component after view initialized.
   */
  ngAfterViewInit() {
    // print array of CustomComponent objects
    // this.componentlist = this.components.toArray();

    this.ALL_FORMS[this.contactForm] = this.components;
  }

  /**
   * Form validate function.
   * @param formname  Name of form fields (#).
   */
  formValidate(formname) {
    this.globalService.formValidate(this.ALL_FORMS[this.contactForm], this.formSubmit, this);
  }

  /**
   * Form submit function (Called after validation).
   * @param self  context value of this
   */
  formSubmit(self) {
    const CONTACT_BODY = JSON.stringify({
      name: self.globalService.formValueForLabel(self.ALL_FORMS[self.contactForm], 'name'),
      email: self.globalService.formValueForLabel(self.ALL_FORMS[self.contactForm], 'email'),
      message: self.globalService.formValueForLabel(self.ALL_FORMS[self.contactForm], 'message'),
    });
    self.apiService.postUrl(self.endpointsService.contactURL(), CONTACT_BODY).subscribe(
      (data) => {
        // Success Message in data.message
        setTimeout(() => self.globalService.showToast('success', data.message, 5), 1000);
        self.router.navigate(['/']);
      },
      (err) => {
        self.globalService.handleFormError(self.components, err, false);
      },
      () => this.logger.info('CONTACT-FORM-SUBMITTED')
    );
  }
}
