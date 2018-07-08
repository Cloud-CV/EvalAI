import { Component, OnInit, Inject } from '@angular/core';
import { ApiService } from '../services/api.service';
import { GlobalService } from '../global.service';
import { DOCUMENT } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-footer',
  templateUrl: './footer.component.html',
  styleUrls: ['./footer.component.scss']
})
export class FooterComponent implements OnInit {
  localRouter: any;
  constructor(private apiService: ApiService, @Inject(DOCUMENT) private document: Document, private globalService: GlobalService,
              private router: Router, private route: ActivatedRoute) { }

  ngOnInit() {
    this.localRouter = this.router;
  }
  getNotifications() {
    const EMAIL = this.document.getElementById('notification-email')['value'];
    if (EMAIL && this.globalService.validateEmail(EMAIL)) {
      this.formSubmit(EMAIL);
    } else {
      this.globalService.showToast('error', 'Invalid Email!');
    }
  }

  formSubmit(email: string) {
    // TODO get notified API path
    const API_PATH = '';
    const BODY = { 'email': email };
    const SELF = this;
    this.apiService.postUrl(API_PATH, JSON.stringify(BODY)).subscribe(
      data => {
        SELF.globalService.showToast('success', 'Subscription successful!');
      },
      err => {
        console.error(err);
        SELF.globalService.showToast('error', 'Subscription failed!');
      },
      () => { }
    );
  }

  navigateTo(url) {
    this.router.navigate([ url ]);
  }

}
