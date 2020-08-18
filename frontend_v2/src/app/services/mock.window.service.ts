import { WindowService } from './window.service';
import { Injectable, Inject } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { NGXLogger } from 'ngx-logger';

@Injectable()
export class MockWindowService extends WindowService {
  constructor(@Inject(DOCUMENT) document: Document, private logger: NGXLogger) {
    super(document);
  }
  /**
   * Mocked Load Javascript function.
   * @param url  Name of script.
   * @param implementationCode  callback function.
   * @param location  where to append the file
   * @param env  `This` variable of the environment
   */
  loadJS(url, implementationCode, location, env) {
    this.logger.info('LoadJS mocked..');
  }
}
