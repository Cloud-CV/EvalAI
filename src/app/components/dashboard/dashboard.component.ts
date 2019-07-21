import {Component, OnDestroy, OnInit} from '@angular/core';
import { ApiService } from '../../services/api.service';
import { GlobalService } from '../../services/global.service';
import { EndpointsService } from '../../services/endpoints.service';
import { AuthService } from '../../services/auth.service';
import { Router, ActivatedRoute } from '@angular/router';

/**
 * Component Class
 */
@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit, OnDestroy {

  /**
   * Authentication Service subscription
   */
  authServiceSubscription: any;

  /**
   * Path for routing
   */
  routePath = '/auth/login';

  /**
   * Constructor.
   * @param endpointsService  EndpointService Injection.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   * @param authService  AuthService Injection.
   */
  constructor(private apiService: ApiService,
              public authService: AuthService,
              private globalService: GlobalService,
              private router: Router,
              private route: ActivatedRoute,
              private endpointsService: EndpointsService) { }

  /**
   * Component on initialized.
   */
  ngOnInit() {
    if (!this.authService.isLoggedIn()) {
      this.router.navigate([this.routePath]);
    }
    this.authServiceSubscription = this.authService.change.subscribe((authState) => {
      if (!authState.isLoggedIn) {
        this.router.navigate([this.routePath]);
      }
    });
  }

  ngOnDestroy(): void {
    if (this.authServiceSubscription) {
      this.authServiceSubscription.unsubscribe();
    }
  }

}
