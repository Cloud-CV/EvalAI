import { Component, OnInit, OnDestroy, HostListener, Inject } from '@angular/core';
import { GlobalService } from './global.service';
import { Router, NavigationEnd, ActivatedRoute } from '@angular/router';
import { DOCUMENT } from '@angular/common';
import { Title } from '@angular/platform-browser';
import 'rxjs/add/operator/filter';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/mergeMap';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})



export class AppComponent implements OnInit, OnDestroy {
  private scrolledState = false;
  globalServiceSubscription: any;
  constructor(
  @Inject(DOCUMENT) private document: Document,
  public router: Router,
  public activatedRoute: ActivatedRoute,
  public titleService: Title,
  private globalService: GlobalService
  ) {
  }

  // Added listener for header scroll event
  @HostListener('window:scroll', [])
    onWindowScroll(): void {
    const HEADER_ELE = document.getElementById('header-static');
    if (this.document.documentElement.scrollTop > 50) {
      if (this.scrolledState === false) {
        this.globalService.scrolledStateChange(true);
      }
    } else {
      if (this.scrolledState === true) {
        this.globalService.scrolledStateChange(false);
      }
    }
    }

  ngOnInit() {
    this.globalServiceSubscription = this.globalService.change.subscribe(scrolledState => {
      this.scrolledState = scrolledState;
    });
    // set page title form routes data
    this.router.events
        // filter for navigation end
      .filter((event) => event instanceof NavigationEnd)
      // check it with current activated route
      .map(() => this.activatedRoute)
      // loop state routes to get the last activated route, first child and return it
      .map((route) => {
            while (route.firstChild) {
              route = route.firstChild;
            }
            return route;
          })
          // filter for primary route
          .filter((route) => route.outlet === 'primary')
        .mergeMap((route) => route.data)
        // set platform based title service
      .subscribe((event) => this.titleService.setTitle(event['title']));
  }
  ngOnDestroy() {
    this.globalServiceSubscription.unsubscribe();
  }
}
