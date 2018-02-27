import { Component, OnInit } from '@angular/core';
import { Router, NavigationEnd, ActivatedRoute } from '@angular/router';
import { Title } from '@angular/platform-browser';
import 'rxjs/add/operator/filter';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/mergeMap';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})

export class AppComponent implements OnInit {
  constructor(
  public router: Router,
  public activatedRoute: ActivatedRoute,
  public titleService: Title
  ) {}

  ngOnInit() {
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
}
