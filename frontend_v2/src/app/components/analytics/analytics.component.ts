import { Component, OnDestroy, OnInit } from '@angular/core';
import { AuthService } from '../../services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-analytics',
  templateUrl: './analytics.component.html',
  styleUrls: ['./analytics.component.scss'],
})
export class AnalyticsComponent implements OnInit, OnDestroy {
  /**
   * Authentication Service subscription
   */
  authServiceSubscription: any;

  constructor(public authService: AuthService, private router: Router) {}

  ngOnInit() {
    this.authService.isLoggedIn();
    this.authServiceSubscription = this.authService.change.subscribe((authState) => {
      if (!authState.isLoggedIn) {
        this.router.navigate(['/auth/login']);
      }
    });
  }

  ngOnDestroy() {
    if (this.authServiceSubscription) {
      this.authServiceSubscription.unsubscribe();
    }
  }
}
