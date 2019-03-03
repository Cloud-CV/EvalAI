import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PubliclistsComponent } from './publiclists.component';
import { ActivatedRoute, Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { GlobalService } from '../../services/global.service';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('PubliclistsComponent', () => {
  let component: PubliclistsComponent;
  let fixture: ComponentFixture<PubliclistsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ PubliclistsComponent ],
      providers: [ GlobalService ],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PubliclistsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
