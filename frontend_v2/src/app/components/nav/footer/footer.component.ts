import { Component, OnInit, Inject, Input } from '@angular/core';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { DOCUMENT } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';

/**
 * Component Class
 */
@Component({
  selector: 'app-footer',
  templateUrl: './footer.component.html',
  styleUrls: ['./footer.component.scss'],
})
export class FooterComponent implements OnInit {
  @Input() isDash = false;

  year: any;

  /**
   * Router local/public instance
   */
  localRouter: any;

  /**
   * URLs where header is transparent
   */
  transparentHeaderUrls = ['', '/'];

  /**
   * Is router at '/'
   */
  atHome = true;

  /**
   * Constructor.
   * @param document  Window document Injection.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   */
  constructor(
    private apiService: ApiService,
    @Inject(DOCUMENT) private document: Document,
    private globalService: GlobalService,
    private router: Router,
    private route: ActivatedRoute
  ) {}

  /**
   * Component on intialized.
   */
  ngOnInit() {
    this.localRouter = this.router;
    this.atHome = true;
    if (!this.transparentHeaderUrls.includes(this.router.url)) {
      this.atHome = false;
    }

    this.year = new Date().getFullYear();
  }

  /**
   * Subscribe for Notifications.
   */
  getNotifications() {
    const EMAIL = this.document.getElementById('notification-email')['value'];
    if (EMAIL && this.globalService.validateEmail(EMAIL)) {
      this.formSubmit(EMAIL);
    } else {
      this.globalService.showToast('error', 'Invalid Email!');
    }
  }

  /**
   * Form Submit function. (called after validation)
   * @param email  email string
   */
  formSubmit(email: string) {
    // TODO get notified API path
    const API_PATH = '';
    const BODY = { email: email };
    const SELF = this;
    this.apiService.postUrl(API_PATH, JSON.stringify(BODY)).subscribe(
      (data) => {
        SELF.globalService.showToast('success', 'Subscription successful!');
      },
      (err) => {
        console.error(err);
        SELF.globalService.showToast('error', 'Subscription failed!');
      },
      () => {}
    );
  }

  /**
   * Navigate to URL.
   * @param url  destination URL path.
   */
  navigateTo(url) {
    this.router.navigate([url]);
  }
}
