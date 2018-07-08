import { Component, OnInit, Inject } from '@angular/core';
import { ViewChildren, QueryList, AfterViewInit } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { InputComponent } from '../input/input.component';
import { WindowService } from '../services/window.service';
import { ApiService } from '../services/api.service';
import { GlobalService } from '../global.service';
import { Router, ActivatedRoute} from '@angular/router';

@Component({
  selector: 'app-contact',
  templateUrl: './contact.component.html',
  styleUrls: ['./contact.component.scss']
})
export class ContactComponent implements OnInit, AfterViewInit {
  API_PATH = 'web/contact/';
  ALL_FORMS: any = {};
  contactForm = 'formgroup';
  @ViewChildren('formgroup')
  components: QueryList<InputComponent>;
  componentlist: any;
  google: any;

  constructor(@Inject(DOCUMENT) private document: Document,
              private windowService: WindowService,
              private globalService: GlobalService,
              private apiService: ApiService,
              private route: ActivatedRoute,
              private router: Router) { }

  ngOnInit() {
    this.loadMapContactPage();
    this.globalService.scrollToTop();
  }

  ngAfterViewInit() {
    // print array of CustomComponent objects
    // this.componentlist = this.components.toArray();

    this.ALL_FORMS[this.contactForm] = this.components;
  }

  formValidate(formname) {
    this.globalService.formValidate(this.ALL_FORMS[this.contactForm], this.formSubmit, this);
  }

  formSubmit(self) {
    const CONTACT_BODY = JSON.stringify({
      name: self.globalService.formValueForLabel(self.ALL_FORMS[self.contactForm], 'name'),
      email: self.globalService.formValueForLabel(self.ALL_FORMS[self.contactForm], 'email'),
      message: self.globalService.formValueForLabel(self.ALL_FORMS[self.contactForm], 'message')
    });
    self.apiService.postUrl(self.API_PATH, CONTACT_BODY).subscribe(
      data => {
        // Success Message in data.message
        setTimeout(() => self.globalService.showToast('success', data.message, 5), 1000);
        self.router.navigate(['']);
      },
      err => {
        self.globalService.showToast('error', err.message, 5);
        console.error(err);
      },
      () => console.log('CONTACT-FORM-SUBMITTED')
    );
  }

  loadMapContactPage() {
    // TODO: Replace this with CloudCV's Google Maps API Key
    const MAP_API_KEY = 'AIzaSyDlXSVBOW9fl96oY4oyTo055jUVd9Y-6dA';

    this.windowService.loadJS('https://maps.googleapis.com/maps/api/js?key=' + MAP_API_KEY,
      this.callBack, this.document.body, this);
  }

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

  callBack(self) {
    self.google = self.windowService.nativeWindow.google;
    self.initMap();
  }

}
