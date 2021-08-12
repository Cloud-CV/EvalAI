import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../../services/auth.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-homemain',
  templateUrl: './homemain.component.html',
  styleUrls: ['./homemain.component.scss'],
})
export class HomemainComponent implements OnInit {
  /**
   * Is user logged in
   */
  isLoggedIn = false;

  /**
   * Constructor.
   * @param authService  AuthService Injection.
   */
  constructor(
    private authService: AuthService
  ) {}

  /**
   * Component on initialized
   */
  ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
  }
}
