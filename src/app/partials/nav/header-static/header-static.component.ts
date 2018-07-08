import { Component, OnInit, OnDestroy, ChangeDetectorRef, Inject, HostListener } from '@angular/core';
import { GlobalService } from '../../../global.service';
import { AuthService } from '../../../services/auth.service';
import { RouterModule, Router, ActivatedRoute, NavigationEnd } from '@angular/router';
import { DOCUMENT } from '@angular/common';

@Component({
  selector: 'app-header-static',
  templateUrl: './header-static.component.html',
  styleUrls: ['./header-static.component.scss']
})
export class HeaderStaticComponent implements OnInit, OnDestroy {
  headerWhite = false;
  // atHome indicates that the page is supposed to have a transparent header like on home.
  transparentHeaderUrls = ['', '/'];
  atHome = true;
  scrolledState = false;
  isMenuExpanded = true;
  globalServiceSubscription: any;
  authServiceSubscription: any;
  authState: any;
  public innerWidth: any;
  constructor(private globalService: GlobalService,
              private route: ActivatedRoute,
              private router: Router,
              private ref: ChangeDetectorRef,
              private authService: AuthService,
              @Inject(DOCUMENT) private document: Document) {
                 this.authState = authService.authState;
              }
  updateElements() {
    this.headerWhite = false;
    this.atHome = true;

    if (!this.transparentHeaderUrls.includes(this.router.url)) {
      this.atHome = false;
      this.headerWhite = true;
    }

    this.globalServiceSubscription = this.globalService.change.subscribe(scrolledState => {
      this.headerWhite = scrolledState || !this.atHome;
      this.scrolledState = scrolledState;
    });
  }
  ngOnInit() {
    this.updateElements();
    this.innerWidth = window.innerWidth;
    if (this.innerWidth <= 810) {
      this.isMenuExpanded = false;
    }
    this.authServiceSubscription = this.authService.change.subscribe((authState) => {
      this.authState = authState;
    });
  }
  @HostListener('window:resize', ['$event'])
  onResize(event) {
    this.innerWidth = window.innerWidth;
    if (this.innerWidth <= 810) {
      this.isMenuExpanded = false;
    }
  }
  sendMeHome() {
    this.atHome = true;
    this.headerWhite = false;
    this.ref.detectChanges();
    this.router.navigate(['']);
  }
  navigateTo(path) {
    this.isMenuExpanded = false;
    this.router.navigate(path);
  }
  ngOnDestroy() {
    this.globalServiceSubscription.unsubscribe();
    this.authServiceSubscription.unsubscribe();
  }
  logIn() {
    this.authService.tryLogIn(null);
  }
  logOut() {
    this.authService.logOut();
  }
  menuExpander() {
    this.isMenuExpanded = !this.isMenuExpanded;
  }

}
