import { Component, OnInit, Inject } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { WindowService } from '../../../services/window.service';
/**
 * Component Class
 */
@Component({
  selector: 'app-twitter-feed',
  templateUrl: './twitter-feed.component.html',
  styleUrls: ['./twitter-feed.component.scss'],
})
export class TwitterFeedComponent implements OnInit {
  /**
   * Component Constructor
   * @param windowService  Window Service injection
   * @param document  Window document Injection.
   */
  constructor(@Inject(DOCUMENT) private document: Document, private windowService: WindowService) {}

  /**
   * Component on initialized
   */
  ngOnInit() {
    this.windowService.loadJS('https://platform.twitter.com/widgets.js', this.feedLoaded, this.document.body, this);
  }

  /**
   * Perform Operations when feed loaded
   */
  feedLoaded(self) {}
}
