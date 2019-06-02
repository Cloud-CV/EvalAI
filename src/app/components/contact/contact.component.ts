import { Component, OnInit, Inject } from '@angular/core';
import { ViewChildren, QueryList, AfterViewInit } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { InputComponent } from '../../components/utility/input/input.component';
import { WindowService } from '../../services/window.service';
import { ApiService } from '../../services/api.service';
import { EndpointsService } from '../../services/endpoints.service';
import { GlobalService } from '../../services/global.service';
import { Router, ActivatedRoute} from '@angular/router';

/**
 * Component Class
 */
@Component({
  selector: 'app-contact',
  templateUrl: './contact.component.html',
  styleUrls: ['./contact.component.scss']
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
   * Google object (initialized after Google maps JS is loaded)
   */
  google: any;

  /**
   * Constructor.
   * @param document  Window document Injection.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   * @param endpointsService  EndpointsService Injection.
   */
  constructor(@Inject(DOCUMENT) private document: Document,
              private windowService: WindowService,
              private globalService: GlobalService,
              private apiService: ApiService,
              private route: ActivatedRoute,
              private router: Router,
              private endpointsService: EndpointsService) { }

  /**
   * Component on initialized.
   */
  ngOnInit() {
    this.loadMapContactPage();
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
      message: self.globalService.formValueForLabel(self.ALL_FORMS[self.contactForm], 'message')
    });
    self.apiService.postUrl(self.endpointsService.contactURL(), CONTACT_BODY).subscribe(
      data => {
        // Success Message in data.message
        setTimeout(() => self.globalService.showToast('success', data.message, 5), 1000);
        self.router.navigate(['/']);
      },
      err => {
        self.globalService.handleFormError(self.components, err, false);
      },
      () => console.log('CONTACT-FORM-SUBMITTED')
    );
  }

  /**
   * Loading Map on the contact page.
   */
  loadMapContactPage() {
    // TODO: Replace this with CloudCV's Google Maps API Key
    const MAP_API_KEY = 'AIzaSyDlXSVBOW9fl96oY4oyTo055jUVd9Y-6dA';

    this.windowService.loadJS('https://maps.googleapis.com/maps/api/js?key=' + MAP_API_KEY,
      this.callBack, this.document.body, this);
  }

  /**
   * Initialize Map parameters.
   */
  initMap() {
    const MAP_CENTER = {lat: 33.779478, lng: -84.434887};
    const MAP_GATECH = {lat: 33.780398, lng: -84.395513};
    const MAP_OBJ = new this.google.maps.Map(document.getElementById('contact-map'), {
          zoom: 13,
          center: MAP_CENTER
    });
    const MAP_MARKER = new this.google.maps.Marker({
      position: MAP_GATECH,
      map: MAP_OBJ
    });
  }

  /**
   * Callback called when Google Map JS is loaded.
   * @param self  context value of this
   */
  callBack(self) {
    self.google = self.windowService.nativeWindow().google;
    self.initMap();
  }

}
