import { Component, OnInit, AfterViewChecked, ChangeDetectorRef } from '@angular/core';
import { AuthService } from '../../services/auth.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-publiclists',
  templateUrl: './publiclists.component.html',
  styleUrls: ['./publiclists.component.scss'],
})
export class PubliclistsComponent implements OnInit, AfterViewChecked {
  isAuth = false;

  /**
   * Constructor.
   * @param authService
   * @param changeDetector
   */
  constructor(public authService: AuthService, private cdRef: ChangeDetectorRef) {}

  /**
   * Component on Initialization.
   */
  ngOnInit() {
    this.isAuth = this.authService.isAuth;
  }

  /**
   * DEV MODE:
   * For resolving change in expression value after it is checked
   */
  ngAfterViewChecked() {
    const isAuth = this.authService.isAuth;
    if (isAuth !== this.isAuth) {
      this.isAuth = isAuth;
      this.cdRef.detectChanges();
    }
  }
}
