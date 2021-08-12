import { Component } from '@angular/core';
import { AuthService } from '../../services/auth.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-publiclists',
  templateUrl: './publiclists.component.html',
  styleUrls: ['./publiclists.component.scss'],
})
export class PubliclistsComponent {
  /**
   * Constructor.
   * @param authService
   */
  constructor(
    public authService: AuthService
  ) {}
}
