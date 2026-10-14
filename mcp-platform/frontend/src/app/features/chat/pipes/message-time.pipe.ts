import { DatePipe } from '@angular/common';
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'messageTime', standalone: true })
export class MessageTimePipe implements PipeTransform {
  private readonly datePipe = new DatePipe('en-US');
  transform(value: string | number | Date): string | null {
    return this.datePipe.transform(value, 'shortTime');
  }
}
